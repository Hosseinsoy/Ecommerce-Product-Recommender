import numpy as np
from scipy import sparse
from lightfm.data import Dataset

from recommendation.ml.feature_engineering import FeatureEngineering


class RecommendationDataset:

    def __init__(self):
        self.fe = FeatureEngineering()

    def _price_bucket(self, price):

        if price < 3_000_000:
            return "price_low"

        elif price < 15_000_000:
            return "price_mid"

        elif price < 50_000_000:
            return "price_high"

        return "price_luxury"

    def _sales_bucket(self, sales):

        if sales == 0:
            return "sales_none"

        elif sales < 5:
            return "sales_low"

        elif sales < 20:
            return "sales_mid"

        return "sales_high"

    def build(self):

        data = self.fe.build_all()

        user_features = data["user_features"]
        item_features = data["item_features"]
        interaction_scores = data["interaction_scores"]

        dataset = Dataset()

        user_feature_tokens = set()
        item_feature_tokens = set()

        # -----------------------------
        # User Features
        # -----------------------------

        for features in user_features.values():

            user_feature_tokens.add(f"age_{features['age']}")
            user_feature_tokens.add(
                self._price_bucket(features["budget"])
            )

            for cat in features["categories"]:
                user_feature_tokens.add(f"cat_{cat}")

            for brand in features["brands"]:
                user_feature_tokens.add(f"brand_{brand}")

        # -----------------------------
        # Item Features
        # -----------------------------

        for features in item_features.values():

            item_feature_tokens.add(
                f"category_{features['category']}"
            )

            item_feature_tokens.add(
                f"brand_{features['brand']}"
            )

            item_feature_tokens.add(
                self._price_bucket(features["price"])
            )

            item_feature_tokens.add(
                self._sales_bucket(features["sales"])
            )

        dataset.fit(

            users=user_features.keys(),

            items=item_features.keys(),

            user_features=user_feature_tokens,

            item_features=item_feature_tokens,

        )

        # -----------------------------
        # Interactions
        # -----------------------------

        interactions = [

            (user, product, score)

            for (user, product), score

            in interaction_scores.items()

        ]

        interaction_matrix, weights = dataset.build_interactions(
            interactions
        )

        # -----------------------------
        # User Feature Matrix
        # -----------------------------

        user_feature_rows = []

        for uid, features in user_features.items():

            feats = [

                f"age_{features['age']}",

                self._price_bucket(features["budget"])

            ]

            feats.extend(
                f"cat_{c}"
                for c in features["categories"]
            )

            feats.extend(
                f"brand_{b}"
                for b in features["brands"]
            )

            user_feature_rows.append(
                (uid, feats)
            )

        user_feature_matrix = dataset.build_user_features(
            user_feature_rows
        )

        # -----------------------------
        # Item Feature Matrix
        # -----------------------------

        item_feature_rows = []

        for pid, features in item_features.items():

            feats = [

                f"category_{features['category']}",

                f"brand_{features['brand']}",

                self._price_bucket(features["price"]),

                self._sales_bucket(features["sales"])

            ]

            item_feature_rows.append(
                (pid, feats)
            )

        item_feature_matrix = dataset.build_item_features(
            item_feature_rows
        )

        return {
            "dataset": dataset,
            "interaction_matrix": interaction_matrix,
            "weights": weights,
            "user_feature_matrix": user_feature_matrix,
            "item_feature_matrix": item_feature_matrix,
            "user_features": user_features,
            "item_features": item_features,
        }