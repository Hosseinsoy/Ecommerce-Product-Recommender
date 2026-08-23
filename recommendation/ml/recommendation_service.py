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

    FINAL_LIMIT = 12


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

        if interaction_count <= 0:
            return (
                0.0,
                1.0
            )

        if interaction_count <= 2:
            return (
                0.30,
                0.70
            )

        if interaction_count <= 5:
            return (
                0.45,
                0.55
            )

        if interaction_count <= 20:
            return (
                0.60,
                0.40
            )

        return (
            0.80,
            0.20
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
            preference=None,
    ):

        number_of_items = len(cls._item_mapping)

        item_weights = {}

        reference_timestamp = timezone.now()

        # -----------------------------
        # Real Interactions
        # -----------------------------

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
                               - interaction.timestamp
                       ).total_seconds() / 86400.0

            age_days = max(age_days, 0)

            decay = math.exp(
                -cls.DECAY_LAMBDA * age_days
            )

            effective_weight = base_weight * decay

            item_weights[product_id] = (
                    item_weights.get(product_id, 0.0)
                    + effective_weight
            )

        # -----------------------------
        # Inject User Preference
        # -----------------------------

        if preference:

            favorite_categories = set(
                preference.favorite_categories.values_list(
                    "id",
                    flat=True
                )
            )

            favorite_brands = set(
                preference.favorite_brands.values_list(
                    "id",
                    flat=True
                )
            )

            preferred_products = Product.objects.filter(
                id__in=cls._item_mapping.keys()
            ).only(
                "id",
                "category_id",
                "brand_id"
            )

            for product in preferred_products:

                if product.id in item_weights:
                    continue

                boost = 0.0

                if product.category_id in favorite_categories:
                    boost += 0.8

                if product.brand_id in favorite_brands:
                    boost += 0.5

                if boost > 0:
                    item_weights[product.id] = boost

        row_indices = []
        row_data = []

        for product_id, weight in item_weights.items():
            row_indices.append(
                cls._item_mapping[product_id]
            )

            row_data.append(weight)

        return sparse.csr_matrix(
            (
                row_data,
                (
                    [0] * len(row_indices),
                    row_indices,
                ),
            ),
            shape=(1, number_of_items),
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

        preference = cls.get_user_preference(user_id)
        interactions = cls.get_user_interactions(user_id)

        # ---------------------------------
        # کاربر بدون هیچ تعاملی
        # ---------------------------------

        if not interactions:
            return cls.preference_fallback(user_id, limit)

        # ---------------------------------
        # ساخت User Row (Interaction + Preference)
        # ---------------------------------

        user_row = cls.build_user_row(
            user_id,
            interactions,
            preference,
        )

        # ---------------------------------
        # Candidate Generation
        # ---------------------------------

        candidate_product_ids = set()

        als_candidates = []

        # ================================
        # 1) ALS Candidates
        # ================================
        interaction_count = len(interactions)
        print(
            "******** DEBUG INTERACTION COUNT ********",
            interaction_count
        )
        if interaction_count <= 2:

            als_candidate_count = 5

        elif interaction_count <= 5:

            als_candidate_count = 10

        elif interaction_count <= 20:

            als_candidate_count = 20

        else:

            als_candidate_count = cls.CANDIDATE_COUNT

        # Disable ALS for low interaction users
        if interaction_count < 10:
            print(
                "******** ALS SHOULD BE DISABLED ********"
            )
            item_indices = []
            als_scores = []

            print(
                "ALS disabled - low interaction count:",
                interaction_count
            )

        else:

            if user_id in cls._user_mapping:

                internal_user_id = cls._user_mapping[user_id]

                item_indices, als_scores = cls._als_model.recommend(
                    internal_user_id,
                    user_row,
                    item_count=als_candidate_count,
                    filter_already_liked_items=True,
                )

            else:

                item_indices, als_scores = cls._als_model.model.recommend(
                    userid=0,
                    user_items=user_row,
                    N=cls.CANDIDATE_COUNT,
                    filter_already_liked_items=True,
                    recalculate_user=True,
                )


        for item_index, score in zip(
                item_indices[:20],
                als_scores[:20]
        ):

            pid = cls._reverse_item_mapping.get(
                int(item_index)
            )

            if pid:
                p = Product.objects.get(
                    id=pid
                )

                print(
                    p.name,
                    score
                )

                if score > 0.15:
                    candidate_product_ids.add(pid)

                    als_candidates.append(
                        (
                            pid,
                            float(score)
                        )
                    )

        # ================================
        # 2) Content Candidates
        # ================================

        scorer = HybridScorer(
            content_model=cls._content_model
        )

        profile = scorer.build_user_profile(
            interactions
        )

        liked_ids = profile.get(
            "liked_product_ids",
            []
        )

        if liked_ids:

            similar_products = Product.objects.filter(

                is_available=True,

                inventory__gt=0,

            ).exclude(

                id__in=liked_ids

            ).select_related(

                "category",
                "brand",

            ).prefetch_related(

                "features",
                "color_variants",
                "size_variants",

            )

            similarity_candidates = []

            for product in similar_products:

                score = scorer.similarity_score(

                    product,

                    profile

                )

                if score > 0:
                    similarity_candidates.append(

                        (
                            product.id,
                            score

                        )

                    )

            similarity_candidates.sort(

                key=lambda x: x[1],

                reverse=True

            )

            for pid, score in similarity_candidates[:50]:
                candidate_product_ids.add(pid)

        # ================================
        # 3) Preference Candidates
        # ================================

        preference_products = cls.preference_fallback(

            user_id,

            limit=5

        )


        for product in preference_products:
            candidate_product_ids.add(
                product.id
            )

        if not candidate_product_ids:
            return cls.interaction_fallback(
                user_id,
                limit
            )

        # تبدیل ALS score ها برای Ranking

        als_score_map = {

            pid: score

            for pid, score

            in als_candidates

        }

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

        candidates = []

        for product in products:
            print(
                "CANDIDATE:",
                product.name,
                "ALS SCORE:",
                als_score_map.get(product.id, 0)
            )
            # اگر interaction کم است ALS را صفر کن
            if interaction_count <= 20:

                candidates.append(
                    (
                        product,
                        0.0
                    )
                )

            else:

                candidates.append(
                    (
                        product,
                        als_score_map.get(
                            product.id,
                            0.0
                        )
                    )
                )

        if not candidates:
            return cls.interaction_fallback(
                user_id,
                limit
            )
        # ---------------------------------
        # Hybrid Ranking
        # ---------------------------------

        if interaction_count <= 10:

            scorer = HybridScorer(
                als_weight=0.0,
                content_weight=1.0,
                content_model=cls._content_model,
            )

        else:

            scorer = HybridScorer(
                als_weight=cls.ALS_WEIGHT,
                content_weight=cls.CONTENT_WEIGHT,
                content_model=cls._content_model,
            )

        profile = scorer.build_user_profile(interactions)

        budget = cls.get_budget(user_id)

        ranked = scorer.rank(
            candidates=candidates,
            profile=profile,
            budget=budget,
            limit=len(candidates),
        )
        interaction_count = len(interactions)

        if interaction_count <= 2:

            behavior_limit = 2

        elif interaction_count <= 5:

            behavior_limit = 5

        else:

            behavior_limit = limit
        # ---------------------------------
        # Dynamic Mixing
        # ---------------------------------

        interaction_count = len(interactions)

        behavior_weight, preference_weight = cls.get_dynamic_weights(
            interaction_count
        )
        print("\n===== FINAL SCORE DEBUG =====")
        # امتیازدهی preference جدا
        for item in ranked:

            preference_score = 0.0

            if preference:
                preference_score = PreferenceScorer.score(
                    item["product"],
                    preference
                )

            item["preference_score"] = preference_score
            print(
                item["product"].name,
                "hybrid:",
                item["hybrid_score"],
                "pref:",
                item["preference_score"]
            )



        # مرتب سازی جداگانه
        behavior_ranked = sorted(
            ranked,
            key=lambda x: x["hybrid_score"],
            reverse=True
        )

        preference_ranked = sorted(
            ranked,
            key=lambda x:
            0.7 * x["hybrid_score"]
            +
            0.3 * x["preference_score"],
            reverse=True
        )

        # تعداد آیتم های رفتاری
        if interaction_count <= 1:

            behavior_count = 2

        elif interaction_count <= 3:

            behavior_count = 4

        elif interaction_count <= 5:

            behavior_count = 6

        else:

            behavior_count = int(
                limit * behavior_weight
            )

        behavior_products = [
            item["product"]
            for item in behavior_ranked[:behavior_count]
        ]

        preference_products = [
            item["product"]
            for item in preference_ranked
            if item["preference_score"] > 0
        ]

        # Merge نهایی
        # Merge نهایی با نسبت واقعی
        print("\n===== PREF PRODUCTS DEBUG =====")

        for p in preference_products[:20]:
            print(p.name)

        print("\n===== BEHAVIOR PRODUCTS DEBUG =====")

        for p in behavior_products:
            print(p.name)
        final_products = []

        behavior_index = 0
        preference_index = 0

        while len(final_products) < limit:

            # 80 درصد رفتار
            if (
                    behavior_index < len(behavior_products)
                    and
                    len(final_products) < int(limit * behavior_weight)
            ):

                product = behavior_products[behavior_index]
                behavior_index += 1

            else:

                if preference_index >= len(preference_products):
                    break

                product = preference_products[preference_index]
                preference_index += 1

            if product not in final_products:
                final_products.append(product)
        print("\n===== PREF SELECTED =====")

        for p in preference_products:
            if "Nintendo" in p.name:
                print("NINTENDO FROM PREF:", p.name)

        print("\n===== BEHAVIOR SELECTED =====")

        for p in behavior_products:
            if "Nintendo" in p.name:
                print("NINTENDO FROM BEHAVIOR:", p.name)
        print("\n===== FINAL PRODUCTS =====")

        for p in final_products:
            print(
                p.name
            )
        return final_products



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