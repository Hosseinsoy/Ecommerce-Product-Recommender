import os
import sys

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

sys.path.append(BASE_DIR)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "SabzShop.settings"
)

import django
django.setup()

from recommendation.ml.feature_engineering import FeatureEngineering

fe = FeatureEngineering()

data = fe.build_all()

print("=" * 50)
print("USER FEATURES:", len(data["user_features"]))
print("ITEM FEATURES:", len(data["item_features"]))
print("INTERACTIONS:", len(data["interaction_scores"]))

print("=" * 50)
print("Sample user:")
uid = next(iter(data["user_features"]))
print(uid, data["user_features"][uid])

print("=" * 50)
print("Sample product:")
pid = next(iter(data["item_features"]))
print(pid, data["item_features"][pid])

print("=" * 50)
print("Sample interaction:")
pair = next(iter(data["interaction_scores"]))
print(pair, data["interaction_scores"][pair])