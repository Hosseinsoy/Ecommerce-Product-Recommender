class PreferenceScorer:

    # =====================================
    # Interaction Weight
    # =====================================

    @staticmethod
    def get_interaction_weight(
        interaction_count
    ):
        """
        تعیین می‌کند UserPreference چقدر
        روی کاربر اثر داشته باشد.

        0 interaction  -> 100%
        1-3            -> 70%
        4-10           -> 40%
        10+             -> 20%
        """

        if interaction_count <= 0:
            return 1.0

        if interaction_count <= 3:
            return 0.70

        if interaction_count <= 10:
            return 0.40

        return 0.20


    # =====================================
    # Explicit Preference Score
    # =====================================

    @staticmethod
    def score(
        product,
        preference
    ):

        if preference is None:
            return 0.0


        favorite_categories = set(
            preference.favorite_categories
            .values_list(
                "id",
                flat=True
            )
        )


        favorite_brands = set(
            preference.favorite_brands
            .values_list(
                "id",
                flat=True
            )
        )


        score = 0.0


        # -----------------------------
        # Favorite Category
        # -----------------------------

        if (
            product.category_id
            and
            product.category_id
            in favorite_categories
        ):

            score += 0.55


        # -----------------------------
        # Favorite Brand
        # -----------------------------

        if (
            product.brand_id
            and
            product.brand_id
            in favorite_brands
        ):

            score += 0.35


        # -----------------------------
        # Budget
        # -----------------------------

        budget = (
            preference.max_monthly_budget
            or 0
        )


        if (
            budget > 0
            and product.price
        ):

            if product.price <= budget:

                score += 0.10

            elif (
                product.price
                <= budget * 1.20
            ):

                score += 0.05


        return min(
            score,
            1.0
        )