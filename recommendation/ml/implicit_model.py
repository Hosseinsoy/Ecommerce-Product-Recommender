import os
import pickle

import implicit


class ImplicitALSModel:

    def __init__(
        self,
        factors=64,
        regularization=0.05,
        iterations=30
    ):

        self.model = implicit.als.AlternatingLeastSquares(
            factors=factors,
            regularization=regularization,
            iterations=iterations,
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
            filter_already_liked_items=True,
            new_user=False
    ):

        user_item_matrix = user_item_matrix.tocsr()

        # ===============================
        # New user
        # ===============================
        if new_user:

            print("ALS: NEW USER MODE")

            user_items = user_item_matrix[0]

            ids, scores = self.model.recommend(
                userid=0,
                user_items=user_items,
                N=item_count,
                filter_already_liked_items=filter_already_liked_items,
                recalculate_user=True
            )


        # ===============================
        # Existing user
        # ===============================
        else:

            user_items = user_item_matrix[user_id]

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