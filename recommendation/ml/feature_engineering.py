from collections import defaultdict

from django.contrib.auth import get_user_model
from django.db.models import Case, Count, IntegerField, Sum, When, Q

from recommendation.models import Interaction, UserPreference
from shop.models import Product

User = get_user_model()

# وزن رویدادها
EVENT_WEIGHTS = {
    "view": 1,
    "wishlist": 3,
    "cart": 5,
    "purchase": 10,
}


class FeatureEngineering:

    def build_user_features(self):
        """
        خروجی:
        {
            user_id:{
                age:int,
                budget:int,
                categories:[...],
                brands:[...]
            }
        }
        """

        result = {}

        preferences = (
            UserPreference.objects
            .prefetch_related(
                "favorite_categories",
                "favorite_brands"
            )
        )

        for pref in preferences:

            result[pref.user_id] = {
                "age": pref.age or 0,
                "budget": pref.max_monthly_budget or 0,
                "categories": [
                    c.name
                    for c in pref.favorite_categories.all()
                ],
                "brands": [
                    b.name
                    for b in pref.favorite_brands.all()
                ]
            }

        return result

    def build_item_features(self):
        """
        خروجی:
        {
            product_id:{
                category:str,
                brand:str,
                price:int,
                sales:int
            }
        }
        """

        result = {}

        products = (
            Product.objects
            .select_related("category", "brand")
            .annotate(
                purchase_count=Count(
                    "interactions",
                    filter=Q(interactions__event="purchase")
                )
            )
        )

        for product in products:
            result[product.id] = {
                "category": product.category.name if product.category else "",
                "brand": product.brand.name if product.brand else "",
                "price": int(product.price),
                "sales": product.purchase_count,
            }

        return result

    def build_interaction_scores(self):
        """
        خروجی:
        {
            (user_id,product_id): score
        }
        """

        weighted = (
            Interaction.objects
            .values(
                "user_id",
                "product_id"
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
                ),
                views=Count("id")
            )
        )

        result = {}

        for row in weighted:

            result[
                (
                    row["user_id"],
                    row["product_id"]
                )
            ] = row["score"]

        return result

    def build_mappings(self):
        """
        ساخت نگاشت id -> index
        """

        users = list(
            User.objects.values_list(
                "id",
                flat=True
            ).order_by("id")
        )

        products = list(
            Product.objects.values_list(
                "id",
                flat=True
            ).order_by("id")
        )

        user_to_index = {
            uid: i
            for i, uid in enumerate(users)
        }

        product_to_index = {
            pid: i
            for i, pid in enumerate(products)
        }

        index_to_user = {
            i: uid
            for uid, i in user_to_index.items()
        }

        index_to_product = {
            i: pid
            for pid, i in product_to_index.items()
        }

        return {
            "user_to_index": user_to_index,
            "product_to_index": product_to_index,
            "index_to_user": index_to_user,
            "index_to_product": index_to_product,
        }

    def build_all(self):

        print("Building user features...")
        user_features = self.build_user_features()

        print("Building item features...")
        item_features = self.build_item_features()

        print("Building interaction scores...")
        interaction_scores = self.build_interaction_scores()

        print("Building mappings...")
        mappings = self.build_mappings()

        print("Done.")

        return {
            "user_features": user_features,
            "item_features": item_features,
            "interaction_scores": interaction_scores,
            "mappings": mappings,
        }