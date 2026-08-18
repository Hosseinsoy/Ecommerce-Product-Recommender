import os
import pickle

import scipy.sparse as sparse

from django.conf import settings
from django.contrib.auth import get_user_model

from recommendation.models import Interaction
from shop.models import Product


User = get_user_model()


class ImplicitDataset:


    def __init__(self):

        self.user_mapping = {}
        self.item_mapping = {}

        self.reverse_user_mapping = {}
        self.reverse_item_mapping = {}



    # =====================================
    # Path
    # =====================================

    def get_mapping_path(self):

        return os.path.join(
            settings.BASE_DIR,
            "recommendation",
            "ml",
            "models"
        )



    # =====================================
    # Weight
    # =====================================

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


    # =====================================
    # Save mappings
    # =====================================

    def save_mappings(self):

        path = self.get_mapping_path()

        os.makedirs(
            path,
            exist_ok=True
        )


        files = {

            "user_mapping.pkl":
                self.user_mapping,

            "reverse_user_mapping.pkl":
                self.reverse_user_mapping,

            "item_mapping.pkl":
                self.item_mapping,

            "reverse_item_mapping.pkl":
                self.reverse_item_mapping,

        }


        for name, data in files.items():

            with open(
                os.path.join(path, name),
                "wb"
            ) as f:

                pickle.dump(
                    data,
                    f
                )


        print("Mappings saved")



    # =====================================
    # Load mappings
    # =====================================

    def load_mappings(self):

        path = self.get_mapping_path()


        files = {

            "user_mapping.pkl":
                "user_mapping",

            "reverse_user_mapping.pkl":
                "reverse_user_mapping",

            "item_mapping.pkl":
                "item_mapping",

            "reverse_item_mapping.pkl":
                "reverse_item_mapping",

        }


        for filename, attr in files.items():

            with open(
                os.path.join(path, filename),
                "rb"
            ) as f:

                setattr(
                    self,
                    attr,
                    pickle.load(f)
                )


        print("Mappings loaded")



    # =====================================
    # Build matrix for training
    # =====================================

    def build_matrix(self):

        print("Building implicit matrix...")


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


        product_ids = (
            interactions
            .values_list(
                "product_id",
                flat=True
            )
            .distinct()
        )


        products = list(

            Product.objects
            .filter(
                id__in=product_ids
            )
            .order_by("id")

        )



        for index, user in enumerate(users):

            self.user_mapping[user.id] = index

            self.reverse_user_mapping[index] = user.id



        for index, product in enumerate(products):

            self.item_mapping[product.id] = index

            self.reverse_item_mapping[index] = product.id



        rows = []
        cols = []
        data = []



        for interaction in interactions:


            if (

                interaction.user_id in self.user_mapping

                and

                interaction.product_id in self.item_mapping

            ):


                rows.append(
                    self.user_mapping[interaction.user_id]
                )


                cols.append(
                    self.item_mapping[interaction.product_id]
                )


                data.append(
                    self.get_weight(
                        interaction.event
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



        self.save_mappings()


        print("==============================")
        print("Users:", len(users))
        print("Items:", len(products))
        print("Interactions:", len(data))
        print("Matrix shape:", matrix.shape)
        print("==============================")


        return matrix



    # =====================================
    # Build matrix for recommendation
    # =====================================

    def build_user_item_matrix(self):


        self.load_mappings()


        interactions = (

            Interaction.objects

            .all()

        )


        rows = []
        cols = []
        data = []



        for interaction in interactions:


            if (

                interaction.user_id in self.user_mapping

                and

                interaction.product_id in self.item_mapping

            ):


                rows.append(
                    self.user_mapping[interaction.user_id]
                )


                cols.append(
                    self.item_mapping[interaction.product_id]
                )


                data.append(
                    self.get_weight(
                        interaction.event
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

                len(self.user_mapping),
                len(self.item_mapping)

            )

        )


        return matrix