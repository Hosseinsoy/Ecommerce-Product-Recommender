import os
import sys

from django.db.models import Count, Avg, Min, Max


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

from django.contrib.auth import get_user_model

from recommendation.models import UserPreference

from shop.models import Category, Brand


User = get_user_model()



# ==========================
# Tests
# ==========================


def line():

    print("=" * 50)



def general_test():

    line()

    print("GENERAL COVERAGE")

    line()


    total_users = User.objects.count()

    preferences = UserPreference.objects.count()


    print(
        "Users:",
        total_users
    )

    print(
        "User Preferences:",
        preferences
    )


    missing = total_users - preferences


    print(
        "Users without preference:",
        missing
    )




def category_coverage():


    line()

    print("CATEGORY PREFERENCE")

    line()


    total_categories = Category.objects.count()


    used_categories = (

        UserPreference.objects

        .filter(
            favorite_categories__isnull=False
        )

        .values(
            "favorite_categories"
        )

        .distinct()

        .count()

    )


    print(
        "Total categories:",
        total_categories
    )


    print(
        "Used in preferences:",
        used_categories
    )



    print(
        "\nTop selected categories:"
    )


    result = (

        UserPreference.objects

        .values(
            "favorite_categories__name"
        )

        .annotate(
            count=Count("id")
        )

        .order_by(
            "-count"
        )

        [:20]

    )


    for item in result:

        print(item)




def brand_coverage():


    line()

    print("BRAND PREFERENCE")

    line()


    total_brands = Brand.objects.count()


    used_brands = (

        UserPreference.objects

        .filter(
            favorite_brands__isnull=False
        )

        .values(
            "favorite_brands"
        )

        .distinct()

        .count()

    )


    print(
        "Total brands:",
        total_brands
    )


    print(
        "Used in preferences:",
        used_brands
    )



    print(
        "\nTop selected brands:"
    )


    result = (

        UserPreference.objects

        .values(
            "favorite_brands__name"
        )

        .annotate(
            count=Count("id")
        )

        .order_by(
            "-count"
        )

        [:20]

    )


    for item in result:

        print(item)




def budget_test():


    line()

    print("BUDGET DISTRIBUTION")

    line()


    data = (

        UserPreference.objects

        .aggregate(

            avg=Avg(
                "max_monthly_budget"
            ),

            minimum=Min(
                "max_monthly_budget"
            ),

            maximum=Max(
                "max_monthly_budget"
            )

        )

    )


    print(data)



    print(
        "\nSample budgets:"
    )


    for pref in (

        UserPreference.objects

        .order_by("?")

        [:20]

    ):

        print(
            {
                "user":
                    pref.user.id,

                "budget":
                    pref.max_monthly_budget,

                "age":
                    pref.age

            }

        )




def user_sample():

    line()

    print("USER SAMPLE")

    line()



    samples = (

        UserPreference.objects

        .select_related(
            "user"
        )

        .prefetch_related(
            "favorite_categories",
            "favorite_brands"
        )

        .order_by("?")

        [:10]

    )


    for pref in samples:


        print(
            {
                "user":
                    pref.user.id,

                "age":
                    pref.age,


                "budget":
                    pref.max_monthly_budget,


                "categories":
                    list(
                        pref.favorite_categories
                        .values_list(
                            "name",
                            flat=True
                        )
                    ),


                "brands":
                    list(
                        pref.favorite_brands
                        .values_list(
                            "name",
                            flat=True
                        )
                    )

            }

        )




def main():


    print(
        "\nUSER PREFERENCE TEST START\n"
    )


    general_test()

    category_coverage()

    brand_coverage()

    budget_test()

    user_sample()


    line()

    print(
        "DONE"
    )

    line()



if __name__ == "__main__":

    main()