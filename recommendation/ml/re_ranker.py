from recommendation.models import UserPreference


class RecommendationReRanker:

    # ==========================
    # Weights
    # ==========================

    CATEGORY_BOOST = 0.15
    BRAND_BOOST = 0.15
    BUDGET_BOOST = 0.10

    DIVERSITY_PENALTY = 0.05

    MAX_SAME_BRAND = 2
    MAX_SAME_CATEGORY = 3

    # ==========================
    # Constructor
    # ==========================

    def __init__(self):

        self.user_preferences = {}

    # ==========================
    # Load User Preference
    # ==========================

    def get_user_preference(self, user_id):

        if user_id in self.user_preferences:

            return self.user_preferences[user_id]

        try:

            preference = (
                UserPreference.objects
                .prefetch_related(
                    "favorite_categories",
                    "favorite_brands"
                )
                .get(
                    user_id=user_id
                )
            )

        except UserPreference.DoesNotExist:

            preference = None

        self.user_preferences[user_id] = preference

        return preference

    # ==========================
    # Category Score
    # ==========================

    def category_boost(
        self,
        product,
        favorite_categories
    ):

        if not product.category:
            return 0.0

        favorite_ids = {
            category.id
            for category in favorite_categories
        }

        if product.category_id in favorite_ids:

            return self.CATEGORY_BOOST

        return 0.0

    # ==========================
    # Brand Score
    # ==========================

    def brand_boost(
        self,
        product,
        favorite_brands
    ):

        if not product.brand:
            return 0.0

        favorite_ids = {
            brand.id
            for brand in favorite_brands
        }

        if product.brand_id in favorite_ids:

            return self.BRAND_BOOST

        return 0.0

    # ==========================
    # Budget Score
    # ==========================

    def budget_boost(
        self,
        product,
        budget
    ):

        if not budget:
            return 0.0

        if not product.price:
            return 0.0

        # کاملاً داخل بودجه
        if product.price <= budget:

            return self.BUDGET_BOOST

        # حداکثر تا 20 درصد بالاتر از بودجه
        if product.price <= budget * 1.20:

            return self.BUDGET_BOOST * 0.5

        return 0.0

    # ==========================
    # Candidate Score
    # ==========================

    def calculate_score(
        self,
        product,
        als_score,
        preference
    ):

        if preference is None:

            return als_score

        score = als_score

        score += self.category_boost(
            product,
            preference.favorite_categories.all()
        )

        score += self.brand_boost(
            product,
            preference.favorite_brands.all()
        )

        score += self.budget_boost(
            product,
            preference.max_monthly_budget
        )

        return score

    # ==========================
    # Re-Rank
    # ==========================

    def rerank(
        self,
        user_id,
        candidates,
        limit=10
    ):

        """
        candidates:
        [
            (Product, als_score),
            ...
        ]

        خروجی:
        [
            {
                "product": Product,
                "score": float
            },
            ...
        ]
        """

        preference = self.get_user_preference(
            user_id
        )

        scored_candidates = []

        for product, als_score in candidates:

            final_score = self.calculate_score(
                product,
                float(als_score),
                preference
            )

            scored_candidates.append(
                {
                    "product": product,
                    "score": final_score,
                    "als_score": float(als_score),
                }
            )

        # ابتدا بر اساس score
        scored_candidates.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        # ==========================
        # Diversity Selection
        # ==========================

        selected = []

        brand_counts = {}
        category_counts = {}

        for candidate in scored_candidates:

            product = candidate["product"]

            brand_id = product.brand_id

            category_id = product.category_id

            # ----------------------
            # Brand limit
            # ----------------------

            if brand_id is not None:

                if (
                    brand_counts.get(
                        brand_id,
                        0
                    )
                    >= self.MAX_SAME_BRAND
                ):

                    continue

            # ----------------------
            # Category limit
            # ----------------------

            if category_id is not None:

                if (
                    category_counts.get(
                        category_id,
                        0
                    )
                    >= self.MAX_SAME_CATEGORY
                ):

                    continue

            selected.append(
                candidate
            )

            if brand_id is not None:

                brand_counts[brand_id] = (
                    brand_counts.get(
                        brand_id,
                        0
                    )
                    + 1
                )

            if category_id is not None:

                category_counts[category_id] = (
                    category_counts.get(
                        category_id,
                        0
                    )
                    + 1
                )

            if len(selected) >= limit:

                break

        return selected