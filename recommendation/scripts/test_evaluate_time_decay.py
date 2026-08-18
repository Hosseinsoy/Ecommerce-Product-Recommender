import os
import sys
import math
import django

import numpy as np
import scipy.sparse as sparse


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

from recommendation.models import Interaction

from recommendation.ml.implicit_dataset import (
    ImplicitDataset
)

from recommendation.ml.implicit_model import (
    ImplicitALSModel
)


# ==========================
# Settings
# ==========================

TEST_EVENTS = {
    "wishlist",
    "cart",
    "purchase",
}

K = 10

DECAY_LAMBDA = 0.061


# ==========================
# Interaction Weights
# ==========================

EVENT_WEIGHTS = {

    "view": 1,

    "wishlist": 3,

    "cart": 5,

    "purchase": 10,

}


# ==========================
# Metrics
# ==========================

def hit_at_k(predictions, target, k=10):

    return 1.0 if target in predictions[:k] else 0.0


def mrr_at_k(predictions, target, k=10):

    for rank, item in enumerate(
        predictions[:k],
        start=1
    ):

        if item == target:

            return 1.0 / rank

    return 0.0


def ndcg_at_k(predictions, target, k=10):

    for rank, item in enumerate(
        predictions[:k],
        start=1
    ):

        if item == target:

            return 1.0 / math.log2(
                rank + 1
            )

    return 0.0


def precision_at_k(predictions, target, k=10):

    if target in predictions[:k]:

        return 1.0 / k

    return 0.0


def recall_at_k(predictions, target, k=10):

    return hit_at_k(
        predictions,
        target,
        k
    )


# ==========================
# Time Decay Weight
# ==========================

def get_decayed_weight(
    interaction,
    reference_timestamp
):

    base_weight = EVENT_WEIGHTS.get(
        interaction.event,
        1
    )


    age_days = (
        reference_timestamp
        - interaction.timestamp
    ).total_seconds() / 86400


    if age_days < 0:

        age_days = 0


    decay = math.exp(
        -DECAY_LAMBDA * age_days
    )


    return base_weight * decay


# ==========================
# Build Mapping
# ==========================

print("==============================")
print("Building mappings")
print("==============================")


dataset = ImplicitDataset()


# build_matrix فقط برای ساخت mapping
# و تعیین ترتیب ثابت user/product استفاده می‌شود.

full_matrix = dataset.build_matrix()


user_mapping = dataset.user_mapping

item_mapping = dataset.item_mapping


print("==============================")


# ==========================
# Build Leave-One-Out
# ==========================

print(
    "Building time-decay Leave-One-Out split..."
)


rows = []
cols = []
data = []


test_targets = {}


users_evaluated = 0


for user_id in user_mapping.keys():


    interactions = list(

        Interaction.objects

        .filter(
            user_id=user_id
        )

        .select_related(
            "product"
        )

        .order_by(
            "timestamp",
            "id"
        )

    )


    if len(interactions) < 2:

        continue


    meaningful = [

        interaction

        for interaction in interactions

        if interaction.event in TEST_EVENTS

    ]


    if not meaningful:

        continue


    # آخرین تعامل معنادار = Test

    test_interaction = meaningful[-1]


    reference_timestamp = (
        test_interaction.timestamp
    )


    # فقط رفتارهای قبل از Test وارد Train می‌شوند

    train_interactions = [

        interaction

        for interaction in interactions

        if (

            interaction.timestamp
            < reference_timestamp

            or (

                interaction.timestamp
                == reference_timestamp

                and

                interaction.id
                < test_interaction.id

            )

        )

    ]


    if not train_interactions:

        continue


    internal_user_id = (
        user_mapping[user_id]
    )


    target_product_id = (
        test_interaction.product_id
    )


    if target_product_id not in item_mapping:

        continue


    target_item_index = (
        item_mapping[target_product_id]
    )


    test_targets[
        internal_user_id
    ] = target_item_index


    # ==========================
    # Train interactions
    # ==========================

    for interaction in train_interactions:


        product_id = (
            interaction.product_id
        )


        if product_id not in item_mapping:

            continue


        weight = get_decayed_weight(

            interaction,

            reference_timestamp

        )


        rows.append(
            internal_user_id
        )


        cols.append(
            item_mapping[product_id]
        )


        data.append(
            weight
        )


    users_evaluated += 1


# ==========================
# Train Matrix
# ==========================

train_matrix = sparse.csr_matrix(

    (
        data,
        (
            rows,
            cols
        )
    ),

    shape=full_matrix.shape

)


print("==============================")
print(
    "Users evaluated:",
    users_evaluated
)
print(
    "Train interactions:",
    len(data)
)
print(
    "Train matrix:",
    train_matrix.shape
)
print(
    "Decay lambda:",
    DECAY_LAMBDA
)
print("==============================")


# ==========================
# Train ALS
# ==========================

print()
print("==============================")
print("Training Time-Decay ALS")
print("==============================")


model = ImplicitALSModel()


model.train(
    train_matrix
)


# ==========================
# Evaluation
# ==========================

print()
print("==============================")
print("Evaluating Time-Decay ALS")
print("==============================")


hits = []
mrrs = []
ndcgs = []
precisions = []
recalls = []


for internal_user_id, target_item in test_targets.items():


    user_items = (

        train_matrix[
            internal_user_id
        ]

        .tocsr()

    )


    item_indices, scores = (

        model.recommend(

            internal_user_id,

            user_items,

            item_count=K,

            filter_already_liked_items=False

        )

    )


    predictions = [

        int(item)

        for item in item_indices

    ]


    hits.append(

        hit_at_k(
            predictions,
            target_item,
            K
        )

    )


    mrrs.append(

        mrr_at_k(
            predictions,
            target_item,
            K
        )

    )


    ndcgs.append(

        ndcg_at_k(
            predictions,
            target_item,
            K
        )

    )


    precisions.append(

        precision_at_k(
            predictions,
            target_item,
            K
        )

    )


    recalls.append(

        recall_at_k(
            predictions,
            target_item,
            K
        )

    )


# ==========================
# Results
# ==========================

print()
print("==============================")
print("TIME-DECAY ALS EVALUATION")
print("==============================")


print(
    f"Users evaluated : {len(hits)}"
)


print(
    f"Decay lambda    : {DECAY_LAMBDA}"
)


print(
    f"HitRate@{K}    : {np.mean(hits):.4f}"
)


print(
    f"Precision@{K} : {np.mean(precisions):.4f}"
)


print(
    f"Recall@{K}    : {np.mean(recalls):.4f}"
)


print(
    f"MRR@{K}       : {np.mean(mrrs):.4f}"
)


print(
    f"NDCG@{K}     : {np.mean(ndcgs):.4f}"
)


print("==============================")