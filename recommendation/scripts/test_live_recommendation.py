import os
import sys
import django


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)


sys.path.append(
    BASE_DIR
)


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "SabzShop.settings"
)


django.setup()


from recommendation.ml.recommendation_service import (
    RecommendationService,
)


USER_ID = 1


print("==============================")
print("Testing live recommendation")
print("==============================")


products = (
    RecommendationService
    .recommend_for_user(
        USER_ID,
        limit=10,
    )
)


print(
    "Recommendations:",
    len(products)
)


print("==============================")


for rank, product in enumerate(
    products,
    start=1
):

    print(
        f"{rank}. "
        f"{product.name} | "
        f"Price={product.price} | "
        f"Category={product.category} | "
        f"Brand={product.brand}"
    )


print("==============================")