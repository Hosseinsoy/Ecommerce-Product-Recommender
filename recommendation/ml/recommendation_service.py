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


    # ALS candidate generation
    ALS_WEIGHT = 0.20

    CONTENT_WEIGHT = 0.80


    # Final behavior vs explicit preference
    BEHAVIOR_WEIGHT = 0.80

    PREFERENCE_WEIGHT = 0.20


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
    # Dynamic Weight
    # =====================================

    @classmethod
    def get_dynamic_weights(
            cls,
            interaction_count
    ):

        """
        تعیین میزان تاثیر رفتار کاربر
        نسبت به UserPreference

        کاربر جدید:
        Preference بیشتر

        با افزایش Interaction:
        رفتار کاربر غالب می‌شود
        """

        if interaction_count <= 0:

            return (
                0.0,
                1.0
            )


        if interaction_count <= 3:

            return (
                0.60,
                0.40
            )


        if interaction_count <= 10:

            return (
                0.80,
                0.20
            )


        return (
            0.90,
            0.10
        )


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
    # Load ALS + Mapping
    # =====================================

    @classmethod
    def load_models(cls):

        if cls._als_model is not None:

            return


        model_dir = cls.model_directory()


        model_path = os.path.join(

            model_dir,

            "final_als_model.pkl",

        )


        if not os.path.exists(model_path):

            raise FileNotFoundError(
                f"ALS model not found: {model_path}"
            )


        als = ImplicitALSModel()


        als.load(
            model_path
        )


        cls._als_model = als


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


        for attribute, filename in mapping_files.items():


            path = os.path.join(

                model_dir,

                filename,

            )


            with open(
                path,
                "rb"
            ) as file:


                setattr(

                    cls,

                    f"_{attribute}",

                    pickle.load(file)

                )


    # =====================================
    # Load Content Model
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


        cls._content_model = ContentSimilarity(

            products

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
                "product__category",
                "product__brand",
            )

            .order_by(
                "timestamp",
                "id",
            )

        )


    # =====================================
    # User Preference
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
    # Build Time Decay User Row
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

        reference_timestamp = timezone.now()


        for interaction in interactions:

            product_id = interaction.product_id


            if product_id not in cls._item_mapping:

                continue


            base_weight = cls.EVENT_WEIGHTS.get(

                interaction.event,

                1.0

            )


            age_days = (

                reference_timestamp
                -
                interaction.timestamp

            ).total_seconds() / 86400.0


            if age_days < 0:

                age_days = 0


            decay = math.exp(

                -cls.DECAY_LAMBDA
                *
                age_days

            )


            effective_weight = (

                base_weight
                *
                decay

            )


            row_indices.append(

                cls._item_mapping[
                    product_id
                ]

            )


            row_data.append(

                effective_weight

            )


        return sparse.csr_matrix(

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



    # =====================================
    # Budget
    # =====================================

    @classmethod
    def get_budget(
            cls,
            user_id,
    ):

        preference = cls.get_user_preference(
            user_id
        )


        if preference is None:

            return 0


        return (

            preference.max_monthly_budget

            or

            0

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


        preference = cls.get_user_preference(
            user_id
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


            score = PreferenceScorer.score(

                product,

                preference

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
    # Interaction Based Cold Start
    # =====================================

    @classmethod
    def interaction_fallback(
            cls,
            user_id,
            limit=10,
    ):


        interactions = cls.get_user_interactions(

            user_id

        )


        preference = cls.get_user_preference(

            user_id

        )


        if not interactions:

            return cls.preference_fallback(

                user_id,

                limit

            )



        seen_product_ids = {

            interaction.product_id

            for interaction in interactions

        }



        products = list(

            Product.objects

            .filter(

                is_available=True,

                inventory__gt=0,

            )

            .exclude(

                id__in=seen_product_ids

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


        if not products:

            return []



        scorer = HybridScorer(

            content_model=cls._content_model

        )


        profile = scorer.build_user_profile(

            interactions

        )


        budget = cls.get_budget(

            user_id

        )



        behavior_weight, preference_weight = (

            cls.get_dynamic_weights(

                len(interactions)

            )

        )



        ranked = []



        for product in products:


            behavior_score = scorer.content_score(

                product,

                profile,

                budget

            )


            preference_score = 0.0


            if preference:

                preference_score = PreferenceScorer.score(

                    product,

                    preference

                )



            final_score = (

                behavior_weight
                *
                behavior_score

                +

                preference_weight
                *
                preference_score

            )


            ranked.append(

                {

                    "product": product,

                    "score": final_score

                }

            )



        ranked.sort(

            key=lambda x: x["score"],

            reverse=True

        )



        return [

            item["product"]

            for item in ranked[:limit]

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



        preference = cls.get_user_preference(
            user_id
        )


        interactions = cls.get_user_interactions(
            user_id
        )



        # =================================
        # New User / Cold Start
        # =================================

        if user_id not in cls._user_mapping:


            if interactions:

                return cls.interaction_fallback(

                    user_id,

                    limit

                )


            return cls.preference_fallback(

                user_id,

                limit

            )



        # =================================
        # User Without Interaction
        # =================================

        if not interactions:

            return cls.preference_fallback(

                user_id,

                limit

            )



        # =================================
        # Build ALS User Row
        # =================================

        user_row = cls.build_user_row(

            user_id,

            interactions

        )


        internal_user_id = cls._user_mapping[user_id]



        # =================================
        # ALS Candidate Generation
        # =================================

        item_indices, als_scores = cls._als_model.recommend(

            internal_user_id,

            user_row,

            item_count=cls.CANDIDATE_COUNT,

            filter_already_liked_items=True,

        )



        candidate_product_ids = []



        for item_index in item_indices:


            item_index = int(item_index)


            if item_index in cls._reverse_item_mapping:


                candidate_product_ids.append(

                    cls._reverse_item_mapping[item_index]

                )



        if not candidate_product_ids:


            return cls.interaction_fallback(

                user_id,

                limit

            )



        # =================================
        # Remove Seen Products
        # =================================

        seen_product_ids = {

            interaction.product_id

            for interaction in interactions

        }



        products = list(

            Product.objects

            .filter(

                id__in=candidate_product_ids,

                is_available=True,

                inventory__gt=0,

            )

            .exclude(

                id__in=seen_product_ids

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



        candidates = []



        for item_index, als_score in zip(

                item_indices,

                als_scores

        ):


            item_index = int(item_index)



            if item_index not in cls._reverse_item_mapping:

                continue



            product_id = cls._reverse_item_mapping[item_index]



            product = products_by_id.get(

                product_id

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


            return cls.interaction_fallback(

                user_id,

                limit

            )



        # =================================
        # Hybrid Profile
        # =================================

        scorer = HybridScorer(

            als_weight=cls.ALS_WEIGHT,

            content_weight=cls.CONTENT_WEIGHT,

            content_model=cls._content_model,

        )


        profile = scorer.build_user_profile(

            interactions

        )



        budget = cls.get_budget(

            user_id

        )



        ranked = scorer.rank(

            candidates=candidates,

            profile=profile,

            budget=budget,

            limit=len(candidates),

        )



        # =================================
        # Dynamic Behavior Preference Blend
        # =================================

        behavior_weight, preference_weight = (

            cls.get_dynamic_weights(

                len(interactions)

            )

        )



        for item in ranked:


            behavior_score = item["hybrid_score"]



            preference_score = 0.0



            if preference:


                preference_score = PreferenceScorer.score(

                    item["product"],

                    preference

                )



            # جلوگیری از غالب شدن preference

            behavior_score = max(

                0.0,

                min(

                    behavior_score,

                    1.0

                )

            )



            preference_score = max(

                0.0,

                min(

                    preference_score,

                    1.0

                )

            )



            item["final_score"] = (

                behavior_weight

                *
                behavior_score

                +

                preference_weight

                *
                preference_score

            )



        ranked.sort(

            key=lambda x: x["final_score"],

            reverse=True

        )



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