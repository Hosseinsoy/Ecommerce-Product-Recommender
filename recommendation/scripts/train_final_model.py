import os
import sys
import math
import django


# ==========================
# Django Setup
# ==========================

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

django.setup()


# ==========================
# Imports
# ==========================

from django.utils import timezone

from recommendation.models import Interaction
from recommendation.ml.implicit_model import ImplicitALSModel

from shop.models import Product

import scipy.sparse as sparse


# ==========================
# Final Model Settings
# ==========================

DECAY_LAMBDA = 0.061

FACTORS = 64
REGULARIZATION = 0.05
ITERATIONS = 30

MODEL_DIR = os.path.join(
    BASE_DIR,
    "recommendation",
    "ml",
    "models"
)


# ==========================
# Interaction Weights
# ==========================

EVENT_WEIGHTS = {
    "view": 1.0,
    "wishlist": 3.0,
    "cart": 5.0,
    "purchase": 10.0,
}


# ==========================
# Build Final Dataset
# ==========================

print("==============================")
print("Building FINAL recommendation dataset")
print("==============================")


interactions = list(
    Interaction.objects
    .select_related(
        "user",
        "product"
    )
    .all()
)


users = list(
    Interaction.objects
    .values_list(
        "user_id",
        flat=True
    )
    .distinct()
    .order_by("user_id")
)


product_ids = list(
    Interaction.objects
    .values_list(
        "product_id",
        flat=True
    )
    .distinct()
    .order_by("product_id")
)


user_mapping = {
    user_id: index
    for index, user_id
    in enumerate(users)
}


item_mapping = {
    product_id: index
    for index, product_id
    in enumerate(product_ids)
}


reverse_user_mapping = {
    index: user_id
    for user_id, index
    in user_mapping.items()
}


reverse_item_mapping = {
    index: product_id
    for product_id, index
    in item_mapping.items()
}


reference_timestamp = timezone.now()


rows = []
cols = []
data = []


for interaction in interactions:

    base_weight = EVENT_WEIGHTS.get(
        interaction.event,
        1.0
    )


    age_days = (
        reference_timestamp
        - interaction.timestamp
    ).total_seconds() / 86400.0


    if age_days < 0:
        age_days = 0


    decay = math.exp(
        -DECAY_LAMBDA * age_days
    )


    weight = (
        base_weight * decay
    )


    rows.append(
        user_mapping[
            interaction.user_id
        ]
    )


    cols.append(
        item_mapping[
            interaction.product_id
        ]
    )


    data.append(
        weight
    )


train_matrix = sparse.csr_matrix(
    (
        data,
        (
            rows,
            cols
        )
    ),
    shape=(
        len(users),
        len(product_ids)
    )
)


print("==============================")
print("Users:", len(users))
print("Items:", len(product_ids))
print("Interactions:", len(interactions))
print("Matrix:", train_matrix.shape)
print("Decay lambda:", DECAY_LAMBDA)
print("==============================")


# ==========================
# Train Final ALS
# ==========================

print()
print("==============================")
print("Training FINAL ALS model")
print("==============================")


model = ImplicitALSModel(
    factors=FACTORS,
    regularization=REGULARIZATION,
    iterations=ITERATIONS
)


model.train(
    train_matrix
)


# ==========================
# Save
# ==========================

os.makedirs(
    MODEL_DIR,
    exist_ok=True
)


model_path = os.path.join(
    MODEL_DIR,
    "final_als_model.pkl"
)


model.save(
    model_path
)


# Save mappings

import pickle


mapping_files = {

    "final_user_mapping.pkl":
        user_mapping,

    "final_reverse_user_mapping.pkl":
        reverse_user_mapping,

    "final_item_mapping.pkl":
        item_mapping,

    "final_reverse_item_mapping.pkl":
        reverse_item_mapping,

}


for filename, mapping in (
    mapping_files.items()
):

    with open(
        os.path.join(
            MODEL_DIR,
            filename
        ),
        "wb"
    ) as f:

        pickle.dump(
            mapping,
            f
        )


print()
print("==============================")
print("FINAL MODEL SAVED")
print("==============================")

print(
    "Model:",
    model_path
)

print(
    "Mappings:",
    MODEL_DIR
)

print("==============================")