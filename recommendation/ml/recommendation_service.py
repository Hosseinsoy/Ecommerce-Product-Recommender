import math
import os
import pickle

import scipy.sparse as sparse

from django.conf import settings
from django.utils import timezone

from recommendation.models import (
    Interaction,
    UserPreference,
)

from recommendation.ml.implicit_model import (
    ImplicitALSModel,
)

from recommendation.ml.hybrid_scorer import (
    HybridScorer,
)

from recommendation.ml.content_similarity import (
    ContentSimilarity,
)

from recommendation.ml.preference_scorer import (
    PreferenceScorer,
)

from shop.models import Product


class RecommendationService:

    # =====================================
    # Final Model Settings
    # =====================================

    DECAY_LAMBDA = 0.061

    CANDIDATE_COUNT = 100

    FINAL_LIMIT = 10

    ALS_WEIGHT = 0.20

    CONTENT_WEIGHT = 0.80


    EVENT_WEIGHTS = {
        "view": 1.0,
        "wishlist": 3.0,
        "cart": 5.0,
        "purchase": 10.0,
    }


    # =====================================
    # Shared Model Cache
    # =====================================

    _als_model = None

    _content_model = None

    _user_mapping = None

    _reverse_user_mapping = None

    _item_mapping = None

    _reverse_item_mapping = None

    _products_loaded = False


    # =====================================
    # Paths
    # =====================================

    @classmethod
    def model_directory(cls):

        return os.path.join(
            settings.BASE_DIR,
            "recommendation",
            "ml",
            "models",
        )


    # =====================================
    # Load ALS + Mappings
    # =====================================

    @classmethod
    def load_models(cls):

        if cls._als_model is not None:
            return


        model_dir = cls.model_directory()


        # -------------------------------
        # ALS Model
        # -------------------------------

        model_path = os.path.join(
            model_dir,
            "final_als_model.pkl",
        )


        if not os.path.exists(model_path):

            raise FileNotFoundError(
                "Final ALS model was not found: "
                f"{model_path}"
            )


        als = ImplicitALSModel()

        als.load(
            model_path
        )


        cls._als_model = als


        # -------------------------------
        # Mappings
        # -------------------------------

        mapping_files = {

            "user_mapping":
                "final_user_mapping.pkl",

            "reverse_user_mapping":
                "final_reverse_user_mapping.pkl",

            "item_mapping":
                "final_item_mapping.pkl",

            "reverse_item_mapping":
                "final_reverse_item_mapping.pkl",

        }


        for attribute, filename in (
            mapping_files.items()
        ):

            path = os.path.join(
                model_dir,
                filename,
            )


            if not os.path.exists(path):

                raise FileNotFoundError(
                    "Recommendation mapping was not found: "
                    f"{path}"
                )


            with open(
                path,
                "rb",
            ) as file:

                setattr(
                    cls,
                    f"_{attribute}",
                    pickle.load(file),
                )


    # =====================================
    # Load Products + Content Model
    # =====================================

    @classmethod
    def load_content_model(cls):

        if cls._products_loaded:
            return


        products = list(

            Product.objects

            .filter(
                id__in=cls._item_mapping.keys()
            )

            .select_related(
                "category",
                "brand",
            )

            .prefetch_related(
                "features",
                "color_variants",
                "size_variants",
            )

        )


        cls._content_model = (
            ContentSimilarity(
                products
            )
        )


        cls._products_loaded = True


    # =====================================
    # User Interactions
    # =====================================

    @classmethod
    def get_user_interactions(
        cls,
        user_id,
    ):

        return list(

            Interaction.objects

            .filter(
                user_id=user_id
            )

            .select_related(
                "product",
            )

            .order_by(
                "timestamp",
                "id",
            )

        )


    # =====================================
    # User Explicit Preference
    # =====================================

    @classmethod
    def get_user_preference(
        cls,
        user_id,
    ):

        try:

            return (

                UserPreference.objects

                .prefetch_related(
                    "favorite_categories",
                    "favorite_brands",
                )

                .get(
                    user_id=user_id
                )

            )

        except UserPreference.DoesNotExist:

            return None


    # =====================================
    # Build Time-Decay User Row
    # =====================================

    @classmethod
    def build_user_row(
        cls,
        user_id,
        interactions,
    ):

        number_of_items = len(
            cls._item_mapping
        )


        row_indices = []

        row_data = []


        reference_timestamp = (
            timezone.now()
        )


        for interaction in interactions:

            product_id = (
                interaction.product_id
            )


            if product_id not in (
                cls._item_mapping
            ):

                continue


            base_weight = (
                cls.EVENT_WEIGHTS.get(
                    interaction.event,
                    1.0,
                )
            )


            age_days = (

                reference_timestamp
                - interaction.timestamp

            ).total_seconds() / 86400.0


            if age_days < 0:

                age_days = 0


            decay = math.exp(
                -cls.DECAY_LAMBDA
                * age_days
            )


            effective_weight = (
                base_weight
                * decay
            )


            row_indices.append(

                cls._item_mapping[
                    product_id
                ]

            )


            row_data.append(
                effective_weight
            )


        matrix = sparse.csr_matrix(

            (
                row_data,
                (
                    [0] * len(row_indices),
                    row_indices,
                ),
            ),

            shape=(
                1,
                number_of_items,
            )

        )


        return matrix


    # =====================================
    # User Budget
    # =====================================

    @classmethod
    def get_budget(
        cls,
        user_id,
    ):

        preference = (
            cls.get_user_preference(
                user_id
            )
        )


        if preference is None:

            return 0


        return (
            preference.max_monthly_budget
            or 0
        )


    # =====================================
    # Preference Fallback
    # =====================================

    @classmethod
    def preference_fallback(
        cls,
        user_id,
        limit=10,
    ):

        preference = (
            cls.get_user_preference(
                user_id
            )
        )


        products = list(

            Product.objects

            .filter(
                is_available=True,
                inventory__gt=0,
            )

            .select_related(
                "category",
                "brand",
            )

        )


        if not products:
            return []


        if preference is None:

            return products[:limit]


        scored_products = []


        for product in products:

            score = (
                PreferenceScorer.score(
                    product,
                    preference
                )
            )


            scored_products.append(
                (
                    product,
                    score
                )
            )


        scored_products.sort(
            key=lambda x: x[1],
            reverse=True
        )


        return [

            product

            for product, score
            in scored_products[:limit]

        ]


    # =====================================
    # Recommendation
    # =====================================

    @classmethod
    def recommend_for_user(
        cls,
        user_id,
        limit=None,
    ):

        cls.load_models()

        cls.load_content_model()


        if limit is None:

            limit = cls.FINAL_LIMIT


        # ---------------------------------
        # User Preference
        # ---------------------------------

        preference = (
            cls.get_user_preference(
                user_id
            )
        )


        # ---------------------------------
        # User Mapping
        # ---------------------------------

        if user_id not in (
            cls._user_mapping
        ):

            return cls.preference_fallback(
                user_id,
                limit
            )


        # ---------------------------------
        # User Interactions
        # ---------------------------------

        interactions = (
            cls.get_user_interactions(
                user_id
            )
        )


        # ---------------------------------
        # Cold Start
        # ---------------------------------

        if not interactions:

            return cls.preference_fallback(
                user_id,
                limit
            )


        # ---------------------------------
        # Determine Preference Weight
        # ---------------------------------

        interaction_count = len(
            interactions
        )


        if preference is None:

            preference_weight = 0.0

        else:

            preference_weight = (
                PreferenceScorer
                .get_interaction_weight(
                    interaction_count
                )
            )


        behavior_weight = (
            1.0
            - preference_weight
        )


        # ---------------------------------
        # User Row
        # ---------------------------------

        user_row = (
            cls.build_user_row(
                user_id,
                interactions,
            )
        )


        # ---------------------------------
        # Internal User ID
        # ---------------------------------

        internal_user_id = (
            cls._user_mapping[
                user_id
            ]
        )


        # ---------------------------------
        # ALS Candidate Generation
        # ---------------------------------

        item_indices, als_scores = (

    cls._als_model.recommend(

        internal_user_id,

        user_row,

        item_count=cls.CANDIDATE_COUNT,

        filter_already_liked_items=True,

    )
)


        candidates = []


        # ---------------------------------
        # Load Candidate Products
        # ---------------------------------

        candidate_product_ids = []


        for item_index in item_indices:

            item_index = int(
                item_index
            )


            if item_index in (
                cls._reverse_item_mapping
            ):

                candidate_product_ids.append(

                    cls._reverse_item_mapping[
                        item_index
                    ]

                )


        if not candidate_product_ids:

            return cls.fallback_products(
                limit
            )


        products = list(

            Product.objects

            .filter(
                id__in=candidate_product_ids,
                is_available=True,
                inventory__gt=0,
            )

            .select_related(
                "category",
                "brand",
            )

            .prefetch_related(
                "features",
                "color_variants",
                "size_variants",
            )

        )


        products_by_id = {
            product.id: product
            for product in products
        }


        # حفظ ترتیب ALS
        # در candidates

        for item_index, als_score in zip(
            item_indices,
            als_scores,
        ):

            item_index = int(
                item_index
            )


            if item_index not in (
                cls._reverse_item_mapping
            ):

                continue


            product_id = (
                cls._reverse_item_mapping[
                    item_index
                ]
            )


            product = (
                products_by_id.get(
                    product_id
                )
            )


            if product is None:

                continue


            candidates.append(
                (
                    product,
                    float(als_score)
                )
            )


        if not candidates:

            return cls.fallback_products(
                limit
            )


        # ---------------------------------
        # Train-based Hybrid Profile
        # ---------------------------------

        scorer = HybridScorer(

            als_weight=cls.ALS_WEIGHT,

            content_weight=cls.CONTENT_WEIGHT,

            content_model=cls._content_model,

        )


        profile = (
            scorer.build_user_profile(
                interactions
            )
        )


        # ---------------------------------
        # Budget
        # ---------------------------------

        budget = cls.get_budget(
            user_id
        )


        # ---------------------------------
        # Hybrid Ranking
        # ---------------------------------

        ranked = scorer.rank(

            candidates=candidates,

            profile=profile,

            budget=budget,

            limit=len(candidates),

        )


        # ---------------------------------
        # Explicit Preference Adjustment
        # ---------------------------------

        for item in ranked:

            explicit_score = (
                PreferenceScorer.score(
                    item["product"],
                    preference
                )
            )


            item[
                "explicit_preference_score"
            ] = explicit_score


            item[
                "final_score"
            ] = (

                behavior_weight
                * item["hybrid_score"]

                +

                preference_weight
                * explicit_score

            )


        # ---------------------------------
        # Final Sort
        # ---------------------------------

        ranked.sort(

            key=lambda x:
            x["final_score"],

            reverse=True

        )


        # ---------------------------------
        # Return Products
        # ---------------------------------

        return [

            item["product"]

            for item in ranked[:limit]

        ]


    # =====================================
    # Generic Fallback
    # =====================================

    @classmethod
    def fallback_products(
        cls,
        limit=10,
    ):

        return list(

            Product.objects

            .filter(
                is_available=True,
                inventory__gt=0,
            )

            .order_by(
                "-created"
            )[:limit]

        )