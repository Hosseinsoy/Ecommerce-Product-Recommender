import math
import django
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
from recommendation.ml.content_similarity import ContentSimilarity
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
    UserPreference,
)

from recommendation.ml.implicit_dataset import (
    ImplicitDataset,
)

from recommendation.ml.implicit_model import (
    ImplicitALSModel,
)

from recommendation.ml.hybrid_scorer import (
    HybridScorer,
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

CANDIDATE_COUNT = 100

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
# Metrics
# ==========================

def hit_at_k(
    predictions,
    target,
    k=10
):

    return (
        1.0
        if target in predictions[:k]
        else 0.0
    )


def mrr_at_k(
    predictions,
    target,
    k=10
):

    for rank, item in enumerate(
        predictions[:k],
        start=1
    ):

        if item == target:

            return 1.0 / rank

    return 0.0


def ndcg_at_k(
    predictions,
    target,
    k=10
):

    for rank, item in enumerate(
        predictions[:k],
        start=1
    ):

        if item == target:

            return 1.0 / math.log2(
                rank + 1
            )

    return 0.0


def precision_at_k(
    predictions,
    target,
    k=10
):

    if target in predictions[:k]:

        return 1.0 / k

    return 0.0


def recall_at_k(
    predictions,
    target,
    k=10
):

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
    reference_timestamp,
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
# User Budget
# ==========================

def get_user_budget(user_id):

    try:

        preference = (
            UserPreference.objects
            .get(
                user_id=user_id
            )
        )


        return (
            preference.max_monthly_budget
            or 0
        )


    except UserPreference.DoesNotExist:

        return 0


# ==========================
# Build Evaluation Split
# ==========================

print("==============================")
print("Building Hybrid Evaluation")
print("==============================")


dataset = ImplicitDataset()


full_matrix = (
    dataset.build_matrix()
)


all_products = list(
    Product.objects
    .select_related(
        "category",
        "brand"
    )
    .prefetch_related(
        "features",
        "color_variants",
        "size_variants"
    )
)


content_model = ContentSimilarity(
    all_products
)


user_mapping = (
    dataset.user_mapping
)


item_mapping = (
    dataset.item_mapping
)


reverse_item_mapping = (
    dataset.reverse_item_mapping
)


# ==========================
# Hybrid Builder
# ==========================

profile_builder = HybridScorer(
    als_weight=0.4,
    content_weight=0.6
)


# ==========================
# Train Matrix Data
# ==========================

rows = []

cols = []

data = []


test_targets = {}

train_profiles = {}

budgets = {}


users_evaluated = 0


# ==========================
# Leave-One-Out Split
# ==========================

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

        if (
            interaction.event
            in TEST_EVENTS
        )

    ]


    if not meaningful:

        continue


    # آخرین تعامل معنادار
    # به عنوان Test

    test_interaction = (
        meaningful[-1]
    )


    reference_timestamp = (
        test_interaction.timestamp
    )


    # فقط interactionهای قبل از Test
    # در Train قرار می‌گیرند

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


    if (
        target_product_id
        not in item_mapping
    ):

        continue


    target_item_index = (
        item_mapping[
            target_product_id
        ]
    )


    test_targets[
        internal_user_id
    ] = target_item_index


    # ==========================
    # Train-only Content Profile
    # ==========================

    train_profiles[
        internal_user_id
    ] = profile_builder.build_user_profile(
        train_interactions
    )


    # ==========================
    # Budget
    # ==========================

    budgets[
        internal_user_id
    ] = get_user_budget(
        user_id
    )


    # ==========================
    # Time-Decay Train Matrix
    # ==========================

    for interaction in train_interactions:


        product_id = (
            interaction.product_id
        )


        if (
            product_id
            not in item_mapping
        ):

            continue


        weight = get_decayed_weight(
            interaction,
            reference_timestamp
        )


        rows.append(
            internal_user_id
        )


        cols.append(
            item_mapping[
                product_id
            ]
        )


        data.append(
            weight
        )


    users_evaluated += 1


# ==========================
# Build Sparse Train Matrix
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

print(
    "Training Time-Decay ALS"
)

print("==============================")


model = ImplicitALSModel()


model.train(
    train_matrix
)


# ==========================
# Hybrid Experiments
# ==========================

ALS_WEIGHTS = [
    0.2,
]


for als_weight in ALS_WEIGHTS:


    print()

    print("==============================")

    print(
        f"HYBRID TEST | ALS={als_weight:.2f}"
    )

    print("==============================")

    hybrid = HybridScorer(
        als_weight=als_weight,
        content_weight=(
                1.0 - als_weight
        ),
        content_model=content_model
    )


    hits = []

    mrrs = []

    ndcgs = []

    precisions = []

    recalls = []


    # ==========================
    # Evaluate Users
    # ==========================

    for (
        internal_user_id,
        target_item
    ) in test_targets.items():


        # --------------------------
        # Train-only interaction row
        # --------------------------

        user_items = (

            train_matrix[
                internal_user_id
            ]

            .tocsr()

        )


        # --------------------------
        # ALS candidates
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


        # --------------------------
        # Convert Items
        # --------------------------

        for (
            item_index,
            als_score
        ) in zip(
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
        # Hybrid Ranking
        # --------------------------

        ranked = hybrid.rank(

            candidates=candidates,

            profile=train_profiles[
                internal_user_id
            ],

            budget=budgets.get(
                internal_user_id,
                0
            ),

            limit=K

        )


        # --------------------------
        # Predictions
        # --------------------------

        predictions = [

            item_mapping[
                candidate["product"].id
            ]

            for candidate in ranked

            if (
                candidate["product"].id
                in item_mapping
            )

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

    print(
        f"Users evaluated : {len(hits)}"
    )


    print(
        f"ALS weight      : {als_weight:.1f}"
    )


    print(
        f"Content weight  : {1.0 - als_weight:.1f}"
    )


    if hits:

        print(
            f"HitRate@{K}    : "
            f"{np.mean(hits):.4f}"
        )


        print(
            f"Precision@{K} : "
            f"{np.mean(precisions):.4f}"
        )


        print(
            f"Recall@{K}    : "
            f"{np.mean(recalls):.4f}"
        )


        print(
            f"MRR@{K}       : "
            f"{np.mean(mrrs):.4f}"
        )


        print(
            f"NDCG@{K}     : "
            f"{np.mean(ndcgs):.4f}"
        )


    else:

        print(
            "No users were successfully evaluated."
        )


    print("==============================")


print()

print("========================================")

print(
    "HYBRID EVALUATION FINISHED"
)

print("========================================")