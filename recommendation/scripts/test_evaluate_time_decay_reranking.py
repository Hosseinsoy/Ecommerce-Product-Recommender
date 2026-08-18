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

from recommendation.models import (
    Interaction,
    UserPreference
)

from recommendation.ml.implicit_dataset import (
    ImplicitDataset
)

from recommendation.ml.implicit_model import (
    ImplicitALSModel
)

from shop.models import Product


# ==========================
# Settings
# ==========================

TEST_EVENTS = {
    "wishlist",
    "cart",
    "purchase",
}

K = 10

CANDIDATE_COUNT = 50

DECAY_LAMBDA = 0.061


# ==========================
# Event Weights
# ==========================

EVENT_WEIGHTS = {

    "view": 1,

    "wishlist": 3,

    "cart": 5,

    "purchase": 10,

}


# ==========================
# Re-ranking Weights
# ==========================

CATEGORY_BOOST = 0.15

BRAND_BOOST = 0.15

BUDGET_BOOST = 0.10


MAX_SAME_BRAND = 2

MAX_SAME_CATEGORY = 3


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
# Time Decay
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
    ).total_seconds() / 86400.0

    if age_days < 0:

        age_days = 0

    decay = math.exp(
        -DECAY_LAMBDA * age_days
    )

    return base_weight * decay


# ==========================
# Build Train-only Preference
# ==========================

def build_train_preference(
    train_interactions
):

    category_scores = {}

    brand_scores = {}


    for interaction in train_interactions:

        weight = EVENT_WEIGHTS.get(
            interaction.event,
            1
        )

        product = interaction.product


        if product.category_id:

            category_scores[
                product.category_id
            ] = (
                category_scores.get(
                    product.category_id,
                    0
                )
                + weight
            )


        if product.brand_id:

            brand_scores[
                product.brand_id
            ] = (
                brand_scores.get(
                    product.brand_id,
                    0
                )
                + weight
            )


    favorite_categories = set(

        sorted(
            category_scores,
            key=category_scores.get,
            reverse=True
        )[:5]

    )


    favorite_brands = set(

        sorted(
            brand_scores,
            key=brand_scores.get,
            reverse=True
        )[:5]

    )


    return {
        "categories": favorite_categories,
        "brands": favorite_brands,
    }


# ==========================
# Budget
# ==========================

def get_budget(user_id):

    try:

        preference = (
            UserPreference.objects
            .get(user_id=user_id)
        )

        return (
            preference.max_monthly_budget
            or 0
        )

    except UserPreference.DoesNotExist:

        return 0


# ==========================
# Candidate Score
# ==========================

def calculate_rerank_score(
    product,
    als_score,
    train_preference,
    budget
):

    score = float(
        als_score
    )


    # Category boost

    if (
        product.category_id
        and
        product.category_id
        in train_preference["categories"]
    ):

        score += CATEGORY_BOOST


    # Brand boost

    if (
        product.brand_id
        and
        product.brand_id
        in train_preference["brands"]
    ):

        score += BRAND_BOOST


    # Budget boost

    if budget:

        if (
            product.price
            and
            product.price <= budget
        ):

            score += BUDGET_BOOST


        elif (
            product.price
            and
            product.price <= budget * 1.20
        ):

            score += (
                BUDGET_BOOST * 0.5
            )


    return score


# ==========================
# Re-ranker
# ==========================

def rerank(
    candidates,
    train_preference,
    budget,
    limit=10
):

    scored = []


    for product, als_score in candidates:

        score = calculate_rerank_score(
            product,
            als_score,
            train_preference,
            budget
        )


        scored.append({

            "product": product,

            "als_score": float(
                als_score
            ),

            "score": score,

        })


    scored.sort(
        key=lambda x: x["score"],
        reverse=True
    )


    selected = []

    brand_counts = {}

    category_counts = {}


    for candidate in scored:

        product = candidate["product"]


        brand_id = product.brand_id

        category_id = product.category_id


        if brand_id is not None:

            if (
                brand_counts.get(
                    brand_id,
                    0
                )
                >= MAX_SAME_BRAND
            ):

                continue


        if category_id is not None:

            if (
                category_counts.get(
                    category_id,
                    0
                )
                >= MAX_SAME_CATEGORY
            ):

                continue


        selected.append(
            candidate
        )


        if brand_id is not None:

            brand_counts[brand_id] = (
                brand_counts.get(
                    brand_id,
                    0
                )
                + 1
            )


        if category_id is not None:

            category_counts[category_id] = (
                category_counts.get(
                    category_id,
                    0
                )
                + 1
            )


        if len(selected) >= limit:

            break


    return selected


# ==========================
# Build Evaluation Split
# ==========================

print("==============================")
print("Building Time-Decay Leave-One-Out")
print("==============================")


dataset = ImplicitDataset()


full_matrix = dataset.build_matrix()


user_mapping = dataset.user_mapping

item_mapping = dataset.item_mapping

reverse_item_mapping = (
    dataset.reverse_item_mapping
)


rows = []

cols = []

data = []


test_targets = {}

train_preferences = {}

train_budgets = {}


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

        if interaction.event
        in TEST_EVENTS

    ]


    if not meaningful:

        continue


    test_interaction = meaningful[-1]


    reference_timestamp = (
        test_interaction.timestamp
    )


    train_interactions = [

        interaction

        for interaction in interactions

        if (

            interaction.timestamp
            < reference_timestamp

            or (

                interaction.timestamp
                == reference_timestamp

                and interaction.id
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


    train_preferences[
        internal_user_id
    ] = build_train_preference(
        train_interactions
    )


    train_budgets[
        internal_user_id
    ] = get_budget(user_id)


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
print("Evaluating Time-Decay + Re-ranking")
print("==============================")


hits = []

mrrs = []

ndcgs = []

precisions = []

recalls = []


for internal_user_id, target_item in (
    test_targets.items()
):

    user_items = (
        train_matrix[
            internal_user_id
        ]
        .tocsr()
    )


    # --------------------------
    # Generate ALS Candidates
    # --------------------------

    item_indices, als_scores = (
        model.recommend(

            internal_user_id,

            user_items,

            item_count=CANDIDATE_COUNT,

            filter_already_liked_items=False

        )
    )


    candidates = []


    for item_index, als_score in zip(
        item_indices,
        als_scores
    ):

        item_index = int(
            item_index
        )


        if (
            item_index
            not in reverse_item_mapping
        ):

            continue


        product_id = (
            reverse_item_mapping[
                item_index
            ]
        )


        try:

            product = (

                Product.objects

                .select_related(
                    "category",
                    "brand"
                )

                .get(
                    id=product_id
                )

            )

        except Product.DoesNotExist:

            continue


        candidates.append(
            (
                product,
                float(als_score)
            )
        )


    if not candidates:

        continue


    # --------------------------
    # Leakage-free Re-ranking
    # --------------------------

    ranked = rerank(

        candidates,

        train_preferences[
            internal_user_id
        ],

        train_budgets.get(
            internal_user_id,
            0
        ),

        limit=K

    )


    predictions = [

        item_mapping[
            candidate["product"].id
        ]

        for candidate in ranked

        if candidate["product"].id
        in item_mapping

    ]


    # --------------------------
    # Metrics
    # --------------------------

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
print("TIME-DECAY + RE-RANKING EVALUATION")
print("==============================")


print(
    f"Users evaluated : {len(hits)}"
)


print(
    f"Candidates/user: {CANDIDATE_COUNT}"
)


print(
    f"Final top-k    : {K}"
)


print(
    f"Decay lambda    : {DECAY_LAMBDA}"
)


if hits:

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

else:

    print(
        "No users were successfully evaluated."
    )


print("==============================")