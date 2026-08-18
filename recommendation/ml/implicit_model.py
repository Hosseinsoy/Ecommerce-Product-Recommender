import os
import pickle

import implicit
from scipy.sparse import csr_matrix


class ImplicitALSModel:


    def __init__(self):

        self.model = implicit.als.AlternatingLeastSquares(

            factors=64,

            regularization=0.05,

            iterations=30,

            random_state=42

        )

    def train(self, interaction_matrix):
        print("==============================")
        print("Training ALS model...")
        print("==============================")

        user_item_matrix = interaction_matrix.tocsr()

        self.model.fit(

            user_item_matrix

        )

        print("Training finished")

    def recommend(

            self,

            user_id,

            user_item_matrix,

            item_count=10

    ):
        user_item_matrix = user_item_matrix.tocsr()

        user_items = user_item_matrix[user_id]

        recommendations = self.model.recommend(

            userid=user_id,

            user_items=user_items,

            N=item_count

        )

        return recommendations


    def save(

        self,

        path

    ):


        os.makedirs(

            os.path.dirname(path),

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



    def load(

        self,

        path

    ):


        with open(

            path,

            "rb"

        ) as f:

            self.model = pickle.load(

                f

            )


        print("Model loaded")