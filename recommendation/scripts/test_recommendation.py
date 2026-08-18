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

from recommendation.ml.implicit_dataset import ImplicitDataset

from recommendation.ml.implicit_model import ImplicitALSModel



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

print("LOADED MODEL USERS:", model.model.user_factors.shape)
print("LOADED MODEL ITEMS:", model.model.item_factors.shape)
print("MAPPING ITEMS:", len(reverse_item_mapping))

print("Model loaded")



# ==========================
# Build matrix
# ==========================

dataset = ImplicitDataset()


user_item_matrix = dataset.build_user_item_matrix()


# ==========================
# Test User
# ==========================

user_id = 1



if user_id not in user_mapping:

    print(
        f"User {user_id} not found"
    )

    exit()



internal_user_id = user_mapping[user_id]



# ==========================
# Recommend
# ==========================

recommendations = model.recommend(

    internal_user_id,

    user_item_matrix,

    item_count=10

)


item_indices, scores = recommendations



print("==============================")
print(
    f"Recommendations for user {user_id}"
)
print("==============================")


for item_index, score in zip(item_indices, scores):
    print(
        "DEBUG ITEM INDEX:",
        item_index,
        "MAX:",
        len(reverse_item_mapping)
    )
    product_id = reverse_item_mapping[item_index]


    product = Product.objects.get(

        id=product_id

    )


    print(

        f"""
Product:
{product.name}

Category:
{product.category}

Brand:
{product.brand}

Price:
{product.price}

Score:
{score}

------------------------------
"""

    )