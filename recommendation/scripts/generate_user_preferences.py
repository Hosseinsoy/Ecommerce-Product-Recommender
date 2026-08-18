import os
import sys
import random


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

import django
django.setup()


# ==========================
# Imports
# ==========================

from django.db.models import Count, Sum, Case, When, IntegerField
from django.contrib.auth import get_user_model

from shop.models import (
    Category,
    Brand,
    Product
)

from recommendation.models import (
    Interaction,
    UserPreference
)

User = get_user_model()


# ==========================
# Settings
# ==========================

MIN_CATEGORY = 1
MAX_CATEGORY = 5

MIN_BRAND = 1
MAX_BRAND = 5


# ==========================
# Budget Generator
# ==========================

def generate_budget():

    budgets = [
        2_000_000,
        5_000_000,
        10_000_000,
        15_000_000,
        20_000_000,
        30_000_000,
        50_000_000,
        80_000_000,
        120_000_000,
        200_000_000
    ]

    weights = [
        10,
        20,
        25,
        20,
        12,
        7,
        4,
        1.5,
        0.4,
        0.1
    ]

    return random.choices(
        budgets,
        weights=weights,
        k=1
    )[0]


# ==========================
# Age Generator
# ==========================

def generate_age():

    return random.randint(
        18,
        60
    )


# ==========================
# Weighted Selection
# ==========================

def weighted_sample(items, weights, count):

    if not items:
        return []

    count = min(count, len(items))

    selected = []
    pool = list(zip(items, weights))

    for _ in range(count):

        total = sum(
            w for _, w in pool
        )

        if total == 0:
            break

        rnd = random.uniform(
            0,
            total
        )

        current = 0

        for item, weight in pool:

            current += weight

            if current >= rnd:

                selected.append(item)
                pool.remove((item, weight))
                break

    return selected


# ==========================
# Category Preference
# ==========================

def get_user_categories(user):

    data = (
        Interaction.objects
        .filter(
            user=user,
            product__category__isnull=False
        )
        .values(
            "product__category"
        )
        .annotate(
            score=Sum(
                Case(
                    When(event="purchase", then=10),
                    When(event="cart", then=5),
                    When(event="wishlist", then=3),
                    default=1,
                    output_field=IntegerField()
                )
            )
        )
        .order_by("-score")
    )

    if data:

        categories = []
        weights = []

        for row in data:

            categories.append(
                Category.objects.get(
                    id=row["product__category"]
                )
            )

            weights.append(
                row["score"]
            )

        return weighted_sample(
            categories,
            weights,
            random.randint(
                MIN_CATEGORY,
                min(MAX_CATEGORY, len(categories))
            )
        )

    all_categories = list(
        Category.objects.all()
    )

    if not all_categories:
        return []

    return random.sample(
        all_categories,
        random.randint(
            MIN_CATEGORY,
            min(MAX_CATEGORY, len(all_categories))
        )
    )


# ==========================
# Brand Preference
# ==========================

def get_user_brands(user, categories):

    if not categories:
        return []

    category_ids = [
        c.id
        for c in categories
    ]

    # ---------- رفتار واقعی کاربر ----------

    data = (
        Interaction.objects
        .filter(
            user=user,
            product__brand__isnull=False,
            product__category__id__in=category_ids
        )
        .values("product__brand")
        .annotate(
            score=Sum(
                Case(
                    When(event="purchase", then=10),
                    When(event="cart", then=5),
                    When(event="wishlist", then=3),
                    default=1,
                    output_field=IntegerField()
                )
            )
        )
        .order_by("-score")
    )

    if data:

        brands = []
        weights = []

        for row in data:

            brands.append(
                Brand.objects.get(
                    id=row["product__brand"]
                )
            )

            weights.append(
                row["score"]
            )

        return weighted_sample(
            brands,
            weights,
            random.randint(
                MIN_BRAND,
                min(MAX_BRAND, len(brands))
            )
        )

    # ---------- Cold Start ----------

    products = (
        Product.objects
        .filter(
            category__id__in=category_ids,
            brand__isnull=False
        )
        .select_related("brand")
    )

    brand_counter = {}

    for product in products:

        brand_counter[product.brand] = (
            brand_counter.get(product.brand, 0) + 1
        )

    if brand_counter:

        brands = list(
            brand_counter.keys()
        )

        weights = list(
            brand_counter.values()
        )

        return weighted_sample(
            brands,
            weights,
            random.randint(
                MIN_BRAND,
                min(MAX_BRAND, len(brands))
            )
        )

    return []


# ==========================
# Main Generator
# ==========================

def generate_preferences():

    print(
        "START USER PREFERENCE GENERATION"
    )

    users = list(
        User.objects.all()
    )

    total = len(users)

    for index, user in enumerate(users, start=1):

        preference, created = (
            UserPreference.objects.get_or_create(
                user=user
            )
        )

        preference.age = generate_age()
        preference.max_monthly_budget = generate_budget()
        preference.save()

        categories = get_user_categories(user)
        preference.favorite_categories.set(categories)

        brands = get_user_brands(
            user,
            categories
        )

        preference.favorite_brands.set(brands)

        if index % 200 == 0:
            print(f"{index}/{total} users processed")

    print("DONE")


# ==========================
# Run
# ==========================

if __name__ == "__main__":
    generate_preferences()