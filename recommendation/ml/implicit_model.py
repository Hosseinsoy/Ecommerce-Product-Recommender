import os
import pickle

import implicit


class ImplicitALSModel:

    def __init__(self):

        self.model = implicit.als.AlternatingLeastSquares(
            factors=64,
            regularization=0.05,
            iterations=30,
            random_state=42
        )

    # =====================================
    # Train
    # =====================================

    def train(self, interaction_matrix):

        print("==============================")
        print("Training ALS model...")
        print("==============================")

        user_item_matrix = interaction_matrix.tocsr()

        self.model.fit(
            user_item_matrix
        )

        print("Training finished")

    # =====================================
    # Recommend
    # =====================================

    def recommend(
        self,
        user_id,
        user_item_matrix,
        item_count=10,
        filter_already_liked_items=True
    ):

        user_item_matrix = user_item_matrix.tocsr()

        # اگر کل ماتریس داده شده باشد
        if user_item_matrix.shape[0] > 1:

            user_items = user_item_matrix[
                user_id
            ]

        # اگر فقط interactionهای یک کاربر داده شده باشد
        else:

            user_items = user_item_matrix

        ids, scores = self.model.recommend(
            userid=user_id,
            user_items=user_items,
            N=item_count,
            filter_already_liked_items=filter_already_liked_items
        )

        return ids, scores

    # =====================================
    # Save
    # =====================================

    def save(self, path):

        directory = os.path.dirname(path)

        if directory:
            os.makedirs(
                directory,
                exist_ok=True
            )

        with open(
            path,
            "wb"
        ) as f:

            pickle.dump(
                self.model,
                f
            )

        print("Model saved")

    # =====================================
    # Load
    # =====================================

    def load(self, path):

        with open(
            path,
            "rb"
        ) as f:

            self.model = pickle.load(
                f
            )

        print("Model loaded")