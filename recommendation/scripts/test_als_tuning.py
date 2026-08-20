import os
import sys
import django
import math
import numpy as np


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

from recommendation.ml.implicit_dataset import ImplicitDataset
from recommendation.ml.time_decay_dataset import TimeDecayDataset
from recommendation.ml.implicit_model import ImplicitALSModel

from recommendation.models import Interaction


# ==========================
# Settings
# ==========================

K = 10

DECAY_LAMBDA = 0.061

TEST_EVENTS = {
    "wishlist",
    "cart",
    "purchase",
}


# ==========================
# Metrics
# ==========================

def hit_at_k(predictions, target):

    return 1 if target in predictions[:K] else 0


def ndcg_at_k(predictions, target):

    for rank, item in enumerate(
        predictions[:K],
        start=1
    ):

        if item == target:
            return 1 / math.log2(rank + 1)

    return 0



# ==========================
# Build Split
# ==========================

print("==============================")
print("Building ALS tuning split")
print("==============================")


dataset = TimeDecayDataset()

matrix = dataset.build_matrix()


user_mapping = dataset.user_mapping
item_mapping = dataset.item_mapping


train_matrix = matrix.copy()


test_targets = {}


for user_id in user_mapping.keys():

    interactions = list(
        Interaction.objects
        .filter(
            user_id=user_id
        )
        .order_by(
            "timestamp",
            "id"
        )
    )


    meaningful = [
        x for x in interactions
        if x.event in TEST_EVENTS
    ]


    if not meaningful:
        continue


    test = meaningful[-1]


    if test.product_id not in item_mapping:
        continue


    user_index = user_mapping[user_id]


    test_targets[user_index] = (
        item_mapping[test.product_id]
    )

    # حذف آخرین تعامل از train
    train_matrix[
        user_index,
        item_mapping[test.product_id]
    ] = 0



print(
    "Users evaluated:",
    len(test_targets)
)


# ==========================
# Grid Search
# ==========================


configs = [

    # factors, reg, iter

    (32, 0.01, 30),
    (64, 0.01, 30),
    (128,0.01,30),

    (64,0.05,30),
    (128,0.05,30),

    (64,0.1,30),
    (128,0.1,30),

    (64,0.05,50),
    (128,0.05,50),

]


results = []


for factors, reg, iterations in configs:


    print()
    print("==============================")
    print(
        f"TEST factors={factors} reg={reg} iter={iterations}"
    )
    print("==============================")


    model = ImplicitALSModel(
        factors=factors,
        regularization=reg,
        iterations=iterations
    )


    model.train(
        train_matrix
    )


    hits=[]
    ndcgs=[]


    for user_id,target in test_targets.items():

        user_items = train_matrix[user_id]


        ids, scores = model.recommend(
            user_id,
            user_items,
            item_count=K,
            filter_already_liked_items=False
        )


        predictions = [
            int(x)
            for x in ids
        ]


        hits.append(
            hit_at_k(
                predictions,
                target
            )
        )


        ndcgs.append(
            ndcg_at_k(
                predictions,
                target
            )
        )



    hit = np.mean(hits)
    ndcg = np.mean(ndcgs)


    print(
        f"HitRate@10 : {hit:.4f}"
    )

    print(
        f"NDCG@10    : {ndcg:.4f}"
    )


    results.append(
        (
            factors,
            reg,
            iterations,
            hit,
            ndcg
        )
    )



# ==========================
# Final Ranking
# ==========================


print()
print("==============================")
print("FINAL RESULTS")
print("==============================")


results.sort(
    key=lambda x:x[4],
    reverse=True
)


for r in results:

    print(
        f"Factors={r[0]} "
        f"Reg={r[1]} "
        f"Iter={r[2]} "
        f"Hit={r[3]:.4f} "
        f"NDCG={r[4]:.4f}"
    )