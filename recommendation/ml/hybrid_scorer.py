from collections import defaultdict
from difflib import SequenceMatcher
import math

from django.utils import timezone

class HybridScorer:

    def __init__(
            self,
            als_weight=0.4,
            content_weight=0.6,
            content_model=None
    ):

        # این دو مقدار از RecommendationService می‌آیند
        # مقدار تست‌شده شما حفظ می‌شود
        self.als_weight = als_weight
        self.content_weight = content_weight

        self.content_model = content_model


    # =====================================
    # Normalize
    # =====================================

    @staticmethod
    def normalize(
            value,
            min_value,
            max_value
    ):

        if max_value <= min_value:
            return 0.0


        return (
            value - min_value
        ) / (
            max_value - min_value
        )


    # =====================================
    # Build User Profile
    # =====================================

    def build_user_profile(
            self,
            train_interactions
    ):

        category_scores = defaultdict(float)

        brand_scores = defaultdict(float)


        total_weight = 0.0

        weighted_price_sum = 0.0


        event_weights = {

            "view": 2.0,

            "wishlist": 5.0,

            "cart": 8.0,

            "purchase": 12.0,

        }


        liked_product_ids = []

        recent_interactions = sorted(
            train_interactions,
            key=lambda x: x.timestamp,
            reverse=True
        )[:20]

        for interaction in recent_interactions:

            event_weight = event_weights.get(

                interaction.event,

                1.0

            )



            # dwell time فقط برای view
            dwell_bonus = 0.0



            if interaction.dwell_time:

                dwell_bonus = min(

                    interaction.dwell_time / 300.0,

                    1.0

                )

            # ===============================
            # Time Decay
            # ===============================

            age_days = (

                               timezone.now()
                               -
                               interaction.timestamp

                       ).total_seconds() / 86400.0

            if age_days < 0:
                age_days = 0

            decay = math.exp(
                -0.15 * age_days
            )

            effective_weight = (
                    event_weight
                    *
                    decay
                    *
                    (
                            1.0
                            +
                            0.25 * dwell_bonus
                    )
            )

            if age_days <= 3:
                effective_weight *= 5


            product = interaction.product



            liked_product_ids.append(

                product.id

            )



            total_weight += effective_weight



            if product.category_id:


                category_scores[

                    product.category_id

                ] += effective_weight



            if product.brand_id:


                brand_scores[

                    product.brand_id

                ] += effective_weight



            if product.price:


                weighted_price_sum += (

                    product.price

                    *

                    effective_weight

                )



        preferred_price = 0.0



        if total_weight > 0:

            preferred_price = (

                weighted_price_sum

                /

                total_weight

            )



        return {


            "category_scores":

                dict(category_scores),



            "brand_scores":

                dict(brand_scores),



            "preferred_price":

                preferred_price,



            "liked_product_ids":

                liked_product_ids,


        }
    # =====================================
    # Category Similarity
    # =====================================

    def category_score(
            self,
            product,
            profile
    ):

        category_scores = profile[
            "category_scores"
        ]


        if not product.category_id:

            return 0.0



        total = sum(
            category_scores.values()
        )



        if total <= 0:

            return 0.0



        return (

            category_scores.get(

                product.category_id,

                0.0

            )

            /

            total

        )


    # =====================================
    # Brand Similarity
    # =====================================

    def brand_score(
            self,
            product,
            profile
    ):

        brand_scores = profile[
            "brand_scores"
        ]



        if not product.brand_id:

            return 0.0



        total = sum(
            brand_scores.values()
        )



        if total <= 0:

            return 0.0



        return (

            brand_scores.get(

                product.brand_id,

                0.0

            )

            /

            total

        )


    # =====================================
    # Price Similarity
    # =====================================

    def price_score(
            self,
            product,
            profile,
            budget
    ):

        if not product.price:

            return 0.0



        preferred_price = profile[

            "preferred_price"

        ]



        if preferred_price <= 0:

            preferred_price = budget



        if preferred_price <= 0:

            return 0.0



        difference = abs(

            product.price

            -

            preferred_price

        )



        return 1.0 / (

            1.0

            +

            (
                difference
                /
                preferred_price
            )

        )


    # =====================================
    # Budget Compatibility
    # =====================================

    def budget_score(
            self,
            product,
            budget
    ):


        if not budget or not product.price:

            return 0.0



        if product.price <= budget:

            return 1.0



        if product.price <= budget * 1.20:

            return 0.5



        return 0.0



    # =====================================
    # Content Similarity
    # =====================================

    def similarity_score(
            self,
            product,
            profile
    ):


        if not self.content_model:

            return 0.0



        liked_product_ids = profile.get(

            "liked_product_ids",

            []

        )



        if not liked_product_ids:

            return 0.0



        return self.content_model.similarity(

            product.id,

            liked_product_ids

        )



    # =====================================
    # Text Similarity
    # =====================================

    def text_similarity(
            self,
            product,
            profile
    ):

        # فعلاً similarity مدل استفاده می‌شود
        # این بخش نگه داشته شده برای توسعه آینده

        return 0.0



    # =====================================
    # Final Content Score
    # =====================================

    def content_score(
            self,
            product,
            profile,
            budget
    ):


        category = self.category_score(

            product,

            profile

        )


        brand = self.brand_score(

            product,

            profile

        )


        price = self.price_score(

            product,

            profile,

            budget

        )


        budget_match = self.budget_score(

            product,

            budget

        )


        similarity = self.similarity_score(

            product,

            profile

        )

        return (

                0.35 * category

                +

                0.15 * brand

                +

                0.10 * price

                +

                0.05 * budget_match

                +

                0.35 * similarity

        )



    # =====================================
    # Hybrid Ranking
    # =====================================

    def rank(
            self,
            candidates,
            profile,
            budget,
            limit=10
    ):


        if not candidates:

            return []



        als_scores = [

            float(score)

            for _, score in candidates

        ]



        min_als = min(als_scores)

        max_als = max(als_scores)



        ranked = []



        for product, als_score in candidates:



            normalized_als = self.normalize(

                float(als_score),

                min_als,

                max_als

            )



            content = self.content_score(

                product,

                profile,

                budget

            )



            hybrid_score = (

                self.als_weight

                *

                normalized_als

                +

                self.content_weight

                *

                content

            )

            print(
                f"""
            PRODUCT: {product.name}
            ALS RAW: {float(als_score):.4f}
            ALS NORMALIZED: {normalized_als:.4f}
            CONTENT SCORE: {content:.4f}
            HYBRID SCORE: {hybrid_score:.4f}
            """
            )


            ranked.append({

                "product": product,


                "als_score": float(

                    als_score

                ),


                "content_score": float(

                    content

                ),


                "hybrid_score": float(

                    hybrid_score

                ),

            })



        ranked.sort(

            key=lambda x:

            x["hybrid_score"],

            reverse=True

        )



        return ranked[:limit]