import os
import sys
import django
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.model_selection import train_test_split

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
from recommendation.ml.implicit_dataset import ImplicitDataset
from recommendation.ml.implicit_model import ImplicitALSModel

# ==========================
# Build Train/Test
# ==========================

print("Building Train/Test split...")

dataset = ImplicitDataset()
full_matrix = dataset.build_matrix()

train_rows = []
train_cols = []
train_data = []

test_dict = {}

users = list(dataset.user_mapping.keys())

for user_id in users:

    interactions = list(
        Interaction.objects.filter(user_id=user_id).order_by("timestamp")
    )

    if len(interactions) < 2:
        continue

    train, test = train_test_split(
        interactions,
        test_size=0.2,
        shuffle=False
    )

    internal_user = dataset.user_mapping[user_id]

    for interaction in train:

        train_rows.append(internal_user)
        train_cols.append(dataset.item_mapping[interaction.product_id])
        train_data.append(dataset.get_weight(interaction.event))

    test_dict[internal_user] = {
        dataset.item_mapping[i.product_id]
        for i in test
    }

train_matrix = csr_matrix(
    (train_data, (train_rows, train_cols)),
    shape=full_matrix.shape
)

print("Train interactions:", len(train_data))
print("Test users:", len(test_dict))

# ==========================
# Train ALS
# ==========================

model = ImplicitALSModel()
model.train(train_matrix)

# ==========================
# Metrics
# ==========================

def precision_at_k(pred, truth, k=10):

    pred = pred[:k]

    if len(pred) == 0:
        return 0

    return len(set(pred) & truth) / k


def recall_at_k(pred, truth, k=10):

    pred = pred[:k]

    if len(truth) == 0:
        return 0

    return len(set(pred) & truth) / len(truth)


def average_precision(pred, truth, k=10):

    score = 0
    hit = 0

    for idx, item in enumerate(pred[:k], start=1):

        if item in truth:
            hit += 1
            score += hit / idx

    if hit == 0:
        return 0

    return score / min(len(truth), k)


def ndcg_at_k(pred, truth, k=10):

    dcg = 0

    for idx, item in enumerate(pred[:k], start=1):

        if item in truth:
            dcg += 1 / np.log2(idx + 1)

    ideal = sum(
        1 / np.log2(i + 2)
        for i in range(min(len(truth), k))
    )

    if ideal == 0:
        return 0

    return dcg / ideal

# ==========================
# Evaluate
# ==========================

precisions = []
recalls = []
maps = []
ndcgs = []

print("Evaluating...")

for internal_user, truth in test_dict.items():

    user_items = train_matrix[internal_user]

    ids, scores = model.recommend(
        internal_user,
        user_items,
        item_count=10
    )

    pred = ids.tolist()

    precisions.append(
        precision_at_k(pred, truth)
    )

    recalls.append(
        recall_at_k(pred, truth)
    )

    maps.append(
        average_precision(pred, truth)
    )

    ndcgs.append(
        ndcg_at_k(pred, truth)
    )

print("\n==============================")
print("ALS Evaluation")
print("==============================")

print(f"Users evaluated : {len(test_dict)}")
print(f"Precision@10    : {np.mean(precisions):.4f}")
print(f"Recall@10       : {np.mean(recalls):.4f}")
print(f"MAP@10          : {np.mean(maps):.4f}")
print(f"NDCG@10         : {np.mean(ndcgs):.4f}")
print("==============================")