import os
import sys
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
from recommendation.ml.time_decay_dataset import TimeDecayDataset
from recommendation.ml.implicit_model import ImplicitALSModel


# ==========================
# Test Event Types
# ==========================

TEST_EVENTS = {
    "wishlist",
    "cart",
    "purchase",
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

            return 1.0 / np.log2(rank + 1)

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
# Build Leave-One-Out Split
# ==========================

print("==============================")
print("Building Leave-One-Out split")
print("==============================")


dataset = TimeDecayDataset()

# اینجا mapping ثابت ساخته و ذخیره می‌شود

full_matrix = dataset.build_matrix()


user_mapping = dataset.user_mapping
item_mapping = dataset.item_mapping


rows = []
cols = []
data = []


test_targets = {}


users_evaluated = 0


for user_id in user_mapping.keys():


    # همه تعاملات کاربر بر اساس زمان

    all_interactions = list(

        Interaction.objects

        .filter(
            user_id=user_id
        )

        .order_by(
            "timestamp"
        )

    )


    if len(all_interactions) < 2:
        continue


    # فقط تعاملات معنادار را برای تست در نظر می‌گیریم

    meaningful_interactions = [

        interaction

        for interaction in all_interactions

        if interaction.event in TEST_EVENTS

    ]


    if not meaningful_interactions:
        continue


    # آخرین interaction معنادار = Test

    test_interaction = (
        meaningful_interactions[-1]
    )


    # تمام تعاملات قبل از target = Train

    train_interactions = [

        interaction

        for interaction in all_interactions

        if interaction.timestamp
        < test_interaction.timestamp

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


        rows.append(
            internal_user_id
        )


        cols.append(
            item_mapping[product_id]
        )


        data.append(
            dataset.get_weight(
                interaction.event
            )
        )


    users_evaluated += 1


# ==========================
# Build Train Matrix
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


# ==========================
# Train ALS
# ==========================

print()
print("==============================")
print("Training evaluation ALS")
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
print("Evaluating")
print("==============================")


K = 10


hits = []
mrrs = []
ndcgs = []
precisions = []
recalls = []


for internal_user_id, target_item in test_targets.items():


    # فقط history مربوط به train

    user_items = (
        train_matrix[
            internal_user_id
        ]
        .tocsr()
    )


    # مهم:
    # target نباید به دلیل filter_already_liked_items حذف شود

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
print("LEAVE-ONE-OUT ALS EVALUATION")
print("==============================")


print(
    f"Users evaluated : {len(test_targets)}"
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