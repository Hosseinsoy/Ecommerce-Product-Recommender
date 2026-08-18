import math

import scipy.sparse as sparse

from django.contrib.auth import get_user_model
from django.utils import timezone

from recommendation.models import Interaction
from recommendation.ml.implicit_dataset import ImplicitDataset


User = get_user_model()


class TimeDecayDataset(ImplicitDataset):

    # ==========================
    # Time Decay Settings
    # ==========================

    DECAY_LAMBDA = 0.01

    # ==========================
    # Interaction Weights
    # ==========================

    def get_weight(self, interaction_type):

        weights = {
            "view": 1,
            "wishlist": 4,
            "cart": 7,
            "purchase": 12,
        }

        return weights.get(
            interaction_type,
            1
        )

    # ==========================
    # Decay Function
    # ==========================

    def get_decayed_weight(self, interaction):

        base_weight = self.get_weight(
            interaction.event
        )

        now = timezone.now()

        age_days = (
            now - interaction.timestamp
        ).total_seconds() / 86400

        if age_days < 0:
            age_days = 0

        decay = math.exp(
            -self.DECAY_LAMBDA * age_days
        )

        return base_weight * decay

    # ==========================
    # Build Matrix
    # ==========================

    def build_matrix(self):

        print(
            "Building time-decay implicit matrix..."
        )

        interactions = (
            Interaction.objects
            .select_related(
                "user",
                "product"
            )
            .all()
        )

        users = list(
            User.objects
            .all()
            .order_by("id")
        )

        # ==========================
        # Stable Product Ordering
        # ==========================

        product_ids = (
            interactions
            .values_list(
                "product_id",
                flat=True
            )
            .distinct()
        )

        from shop.models import Product

        products = list(
            Product.objects
            .filter(
                id__in=product_ids
            )
            .order_by("id")
        )

        # ==========================
        # User Mapping
        # ==========================

        self.user_mapping.clear()
        self.reverse_user_mapping.clear()

        for index, user in enumerate(users):

            self.user_mapping[user.id] = index

            self.reverse_user_mapping[index] = user.id

        # ==========================
        # Item Mapping
        # ==========================

        self.item_mapping.clear()
        self.reverse_item_mapping.clear()

        for index, product in enumerate(products):

            self.item_mapping[product.id] = index

            self.reverse_item_mapping[index] = product.id

        # ==========================
        # Sparse Matrix
        # ==========================

        rows = []
        cols = []
        data = []

        for interaction in interactions:

            user_id = interaction.user_id
            product_id = interaction.product_id

            if (
                user_id in self.user_mapping
                and
                product_id in self.item_mapping
            ):

                rows.append(
                    self.user_mapping[user_id]
                )

                cols.append(
                    self.item_mapping[product_id]
                )

                data.append(
                    self.get_decayed_weight(
                        interaction
                    )
                )

        matrix = sparse.csr_matrix(
            (
                data,
                (
                    rows,
                    cols
                )
            ),
            shape=(
                len(users),
                len(products)
            )
        )

        print("==============================")
        print("Users:", len(users))
        print("Items:", len(products))
        print(
            "Interactions:",
            len(data)
        )
        print(
            "Matrix shape:",
            matrix.shape
        )
        print(
            "Decay lambda:",
            self.DECAY_LAMBDA
        )
        print(
            "Weights:",
            "view=1, wishlist=4, cart=7, purchase=12"
        )
        print("==============================")

        return matrix