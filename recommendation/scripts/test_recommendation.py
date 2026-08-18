import os
import sys
import django
import pickle


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

from shop.models import Product

from recommendation.ml.implicit_dataset import (
    ImplicitDataset
)

from recommendation.ml.implicit_model import (
    ImplicitALSModel
)

from recommendation.ml.re_ranker import (
    RecommendationReRanker
)


# ==========================
# Paths
# ==========================

MODEL_DIR = os.path.join(
    BASE_DIR,
    "recommendation",
    "ml",
    "models"
)


# ==========================
# Load mappings
# ==========================

print("==============================")
print("Loading mappings...")
print("==============================")


with open(
    os.path.join(
        MODEL_DIR,
        "user_mapping.pkl"
    ),
    "rb"
) as f:

    user_mapping = pickle.load(f)


with open(
    os.path.join(
        MODEL_DIR,
        "reverse_item_mapping.pkl"
    ),
    "rb"
) as f:

    reverse_item_mapping = pickle.load(f)


print("Mappings loaded")


# ==========================
# Load model
# ==========================

model = ImplicitALSModel()


model.load(
    os.path.join(
        MODEL_DIR,
        "als_model.pkl"
    )
)


# ==========================
# Build Matrix
# ==========================

dataset = ImplicitDataset()

user_item_matrix = (
    dataset.build_user_item_matrix()
)


# ==========================
# Test User
# ==========================

user_id = 1


if user_id not in user_mapping:

    print(
        f"User {user_id} not found"
    )

    raise SystemExit


internal_user_id = (
    user_mapping[user_id]
)


# ==========================
# ALS Candidates
# ==========================

item_indices, scores = model.recommend(
    internal_user_id,
    user_item_matrix,
    item_count=50,
    filter_already_liked_items=True
)


candidates = []


for item_index, als_score in zip(
    item_indices,
    scores
):

    item_index = int(item_index)

    product_id = reverse_item_mapping[
        item_index
    ]

    try:

        product = Product.objects.select_related(
            "category",
            "brand"
        ).get(
            id=product_id
        )

    except Product.DoesNotExist:

        continue

    candidates.append(
        (
            product,
            float(als_score)
        )
    )


# ==========================
# Re-Ranking
# ==========================

reranker = (
    RecommendationReRanker()
)


recommendations = reranker.rerank(
    user_id=user_id,
    candidates=candidates,
    limit=10
)


# ==========================
# Print Results
# ==========================

print("==============================")
print(
    f"Re-ranked Recommendations for user {user_id}"
)
print("==============================")


for rank, recommendation in enumerate(
    recommendations,
    start=1
):

    product = recommendation["product"]

    final_score = recommendation["score"]

    als_score = recommendation["als_score"]

    print(
        f"""
Rank:
{rank}

Product:
{product.name}

Category:
{product.category}

Brand:
{product.brand}

Price:
{product.price}

ALS Score:
{als_score:.4f}

Final Score:
{final_score:.4f}

------------------------------
"""
    )