from collections import defaultdict


class HybridScorer:

    def __init__(
        self,
        als_weight=0.4,
        content_weight=0.6
    ):

        self.als_weight = als_weight
        self.content_weight = content_weight

    # =====================================
    # Normalize
    # =====================================

    @staticmethod
    def normalize(value, min_value, max_value):

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

        product_price_scores = defaultdict(float)

        total_weight = 0.0

        for interaction in train_interactions:

            event_weight = {
                "view": 1.0,
                "wishlist": 3.0,
                "cart": 5.0,
                "purchase": 10.0,
            }.get(
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

            effective_weight = (
                event_weight
                * (
                    1.0
                    + 0.25 * dwell_bonus
                )
            )

            product = interaction.product

            total_weight += effective_weight

            # Category
            if product.category_id:

                category_scores[
                    product.category_id
                ] += effective_weight

            # Brand
            if product.brand_id:

                brand_scores[
                    product.brand_id
                ] += effective_weight

            # Price preference
            if product.price:

                product_price_scores[
                    product.id
                ] += effective_weight

        # میانگین قیمت تعاملات کاربر
        weighted_price = 0.0

        if total_weight > 0:

            for product_id, weight in (
                product_price_scores.items()
            ):

                try:

                    product = train_interactions[
                        0
                    ].product.__class__.objects.get(
                        id=product_id
                    )

                    weighted_price += (
                        product.price
                        * weight
                    )

                except Exception:
                    continue

            weighted_price /= total_weight

        return {
            "category_scores": dict(
                category_scores
            ),
            "brand_scores": dict(
                brand_scores
            ),
            "preferred_price": weighted_price,
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
            / total
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
            / total
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

        # اگر interaction کافی برای
        # تخمین قیمت نداریم، بودجه را جایگزین کن
        if preferred_price <= 0:

            preferred_price = budget

        if preferred_price <= 0:
            return 0.0

        difference = abs(
            product.price
            - preferred_price
        )

        # similarity در بازه 0 تا 1
        similarity = 1.0 / (
            1.0
            + (
                difference
                / preferred_price
            )
        )

        return similarity

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

        # حداکثر 20٪ بالاتر از بودجه
        if product.price <= budget * 1.20:
            return 0.5

        # محصولات خیلی گران امتیاز صفر
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

        # وزن داخلی Content
        return (
            0.35 * category
            + 0.25 * brand
            + 0.20 * price
            + 0.20 * budget_match
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
                * normalized_als
                +
                self.content_weight
                * content
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