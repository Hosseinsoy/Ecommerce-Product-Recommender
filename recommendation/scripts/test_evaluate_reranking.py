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
from recommendation.ml.implicit_dataset import ImplicitDataset
from recommendation.ml.implicit_model import ImplicitALSModel

from shop.models import Product


# ==========================
# Evaluation Settings
# ==========================

TEST_EVENTS = {
    "wishlist",
    "cart",
    "purchase",
}

K = 10

CANDIDATE_COUNT = 50


# ==========================
# Re-ranking Settings
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
# Train Preference Builder
# ==========================

def build_train_preference(train_interactions):

    """
    Preference ساخته شده فقط از interactionهای Train.

    خروجی:
    {
        "category_ids": set(...),
        "brand_ids": set(...),
    }
    """

    category_scores = {}
    brand_scores = {}

    event_weights = {
        "view": 1,
        "wishlist": 3,
        "cart": 5,
        "purchase": 10,
    }


    for interaction in train_interactions:

        weight = event_weights.get(
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


    # مثل Preference واقعی:
    # دسته‌ها و برندهای دارای امتیاز بالاتر را نگه می‌داریم.

    category_ids = set(

        sorted(
            category_scores,
            key=category_scores.get,
            reverse=True
        )[:5]

    )


    brand_ids = set(

        sorted(
            brand_scores,
            key=brand_scores.get,
            reverse=True
        )[:5]

    )


    return {

        "category_ids": category_ids,

        "brand_ids": brand_ids,

    }


# ==========================
# Budget Boost
# ==========================

def budget_boost(product, budget):

    if not budget:
        return 0.0


    if not product.price:
        return 0.0


    if product.price <= budget:

        return BUDGET_BOOST


    if product.price <= budget * 1.20:

        return BUDGET_BOOST * 0.5


    return 0.0


# ==========================
# Re-ranking
# ==========================

def rerank_candidates(
    candidates,
    train_preference,
    budget,
    limit=10
):

    """
    candidates:
    [
        (product, als_score),
        ...
    ]
    """

    category_ids = (
        train_preference["category_ids"]
    )


    brand_ids = (
        train_preference["brand_ids"]
    )


    scored = []


    for product, als_score in candidates:

        final_score = float(
            als_score
        )


        # Category boost

        if (
            product.category_id
            and
            product.category_id in category_ids
        ):

            final_score += CATEGORY_BOOST


        # Brand boost

        if (
            product.brand_id
            and
            product.brand_id in brand_ids
        ):

            final_score += BRAND_BOOST


        # Budget boost

        final_score += budget_boost(
            product,
            budget
        )


        scored.append({

            "product": product,

            "als_score": float(
                als_score
            ),

            "score": final_score,

        })


    # ALS + preference score

    scored.sort(
        key=lambda x: x["score"],
        reverse=True
    )


    # ==========================
    # Diversity
    # ==========================

    selected = []

    brand_counts = {}

    category_counts = {}


    for candidate in scored:

        product = candidate["product"]


        brand_id = (
            product.brand_id
        )


        category_id = (
            product.category_id
        )


        # Brand limit

        if brand_id is not None:

            if (
                brand_counts.get(
                    brand_id,
                    0
                )
                >= MAX_SAME_BRAND
            ):

                continue


        # Category limit

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
# Build Leave-One-Out Split
# ==========================

print("==============================")
print("Building Leakage-Free Leave-One-Out split")
print("==============================")


dataset = ImplicitDataset()


full_matrix = dataset.build_matrix()


user_mapping = dataset.user_mapping


item_mapping = dataset.item_mapping


reverse_user_mapping = (
    dataset.reverse_user_mapping
)


# Train matrix

rows = []
cols = []
data = []


# Test targets

test_targets = {}


# Train-only preferences

train_preferences = {}


# Train-only budgets

train_budgets = {}


users_evaluated = 0


users = list(
    user_mapping.keys()
)


for user_id in users:


    # --------------------------------
    # Complete chronological history
    # --------------------------------

    all_interactions = list(

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


    if len(all_interactions) < 2:

        continue


    # --------------------------------
    # Meaningful interactions
    # --------------------------------

    meaningful_interactions = [

        interaction

        for interaction in all_interactions

        if interaction.event in TEST_EVENTS

    ]


    if not meaningful_interactions:

        continue


    # --------------------------------
    # Last meaningful interaction = Test
    # --------------------------------

    test_interaction = (
        meaningful_interactions[-1]
    )


    # --------------------------------
    # Everything before Test = Train
    # --------------------------------

    train_interactions = [

        interaction

        for interaction in all_interactions

        if (

            interaction.timestamp
            < test_interaction.timestamp

            or (

                interaction.timestamp
                == test_interaction.timestamp

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


    # --------------------------------
    # Build Train-only preference
    # --------------------------------

    train_preferences[
        internal_user_id
    ] = build_train_preference(
        train_interactions
    )


    # --------------------------------
    # Budget
    #
    # Budget is static user information,
    # not derived from future interactions.
    # --------------------------------

    try:

        from recommendation.models import (
            UserPreference
        )


        preference = (
            UserPreference.objects
            .get(
                user_id=user_id
            )
        )


        train_budgets[
            internal_user_id
        ] = preference.max_monthly_budget


    except UserPreference.DoesNotExist:

        train_budgets[
            internal_user_id
        ] = 0


    # --------------------------------
    # Add Train interactions
    # --------------------------------

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
print("Evaluating Leakage-Free Re-ranking")
print("==============================")


hits = []
mrrs = []
ndcgs = []
precisions = []
recalls = []


for internal_user_id, target_item in test_targets.items():


    # --------------------------------
    # User's TRAIN history only
    # --------------------------------

    user_items = (
        train_matrix[
            internal_user_id
        ]
        .tocsr()
    )


    # --------------------------------
    # ALS candidates
    # --------------------------------

    item_indices, als_scores = (

        model.recommend(

            internal_user_id,

            user_items,

            item_count=CANDIDATE_COUNT,

            filter_already_liked_items=False

        )

    )


    candidates = []


    # --------------------------------
    # Convert indices → Products
    # --------------------------------

    for item_index, als_score in zip(
        item_indices,
        als_scores
    ):


        item_index = int(
            item_index
        )


        if item_index not in (
            dataset.reverse_item_mapping
        ):

            continue


        product_id = (
            dataset.reverse_item_mapping[
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


    # --------------------------------
    # Leakage-free Re-ranking
    # --------------------------------

    ranked = rerank_candidates(

        candidates=candidates,

        train_preference=(
            train_preferences[
                internal_user_id
            ]
        ),

        budget=(
            train_budgets.get(
                internal_user_id,
                0
            )
        ),

        limit=K

    )


    predictions = []


    for candidate in ranked:


        product_id = (
            candidate["product"].id
        )


        if product_id not in item_mapping:

            continue


        predictions.append(

            item_mapping[
                product_id
            ]

        )


    # --------------------------------
    # Metrics
    # --------------------------------

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
print("LEAKAGE-FREE RE-RANKING EVALUATION")
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