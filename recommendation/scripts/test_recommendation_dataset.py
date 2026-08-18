import os
import sys


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



from django.db.models import (
    Count,
    Avg,
    Max,
    Min,
    Sum
)


from django.db.models.functions import TruncMonth


from recommendation.models import Interaction



# ==========================
# Utils
# ==========================


def section(title):

    print("\n")
    print("=" * 40)
    print(title)
    print("=" * 40)



# ==========================
# 1. Coverage
# ==========================


def coverage_test():

    section(
        "GENERAL COVERAGE"
    )


    qs = Interaction.objects.all()


    print(
        "Total interactions:",
        qs.count()
    )


    print(
        "Unique users:",
        qs.values(
            "user_id"
        ).distinct().count()
    )


    print(
        "Unique products:",
        qs.values(
            "product_id"
        ).distinct().count()
    )


    print(
        "Unique sessions:",
        qs.values(
            "session_id"
        ).distinct().count()
    )



# ==========================
# 2. Event Distribution
# ==========================


def event_test():

    section(
        "EVENT DISTRIBUTION"
    )


    data = (

        Interaction.objects

        .values(
            "event"
        )

        .annotate(
            count=Count("id")
        )

        .order_by(
            "event"
        )

    )


    for item in data:

        print(item)



# ==========================
# 3. Source Distribution
# ==========================


def source_test():

    section(
        "SOURCE DISTRIBUTION"
    )


    data=(

        Interaction.objects

        .values(
            "source"
        )

        .annotate(
            count=Count("id")
        )

        .order_by(
            "-count"
        )

    )


    for item in data:

        print(item)



# ==========================
# 4. Search Quality
# ==========================


def search_test():

    section(
        "SEARCH QUALITY"
    )


    total = Interaction.objects.count()


    with_query=(

        Interaction.objects

        .exclude(
            search_query=None
        )

        .count()

    )


    without_query = total - with_query



    print(
        "With search query:",
        with_query
    )


    print(
        "Without search query:",
        without_query
    )



    print(
        "\nSearch events:"
    )


    data=(

        Interaction.objects

        .exclude(
            search_query=None
        )

        .values(
            "event"
        )

        .annotate(
            count=Count("id")
        )

    )


    for item in data:

        print(item)



# ==========================
# 5. Conversion Funnel
# ==========================


def conversion_test():

    section(
        "CONVERSION FUNNEL"
    )


    views = Interaction.objects.filter(
        event="view"
    ).count()


    wishlist = Interaction.objects.filter(
        event="wishlist"
    ).count()


    cart = Interaction.objects.filter(
        event="cart"
    ).count()


    purchase = Interaction.objects.filter(
        event="purchase"
    ).count()



    print(
        "Views:",
        views
    )


    print(
        "Wishlist:",
        wishlist
    )


    print(
        "Cart:",
        cart
    )


    print(
        "Purchase:",
        purchase
    )



    if views:

        print(
            "View -> Wishlist:",
            round(
                wishlist/views*100,
                2
            ),
            "%"
        )


        print(
            "View -> Cart:",
            round(
                cart/views*100,
                2
            ),
            "%"
        )



    if cart:

        print(
            "Cart -> Purchase:",
            round(
                purchase/cart*100,
                2
            ),
            "%"
        )



# ==========================
# 6. Session Quality
# ==========================


def session_test():

    section(
        "SESSION QUALITY"
    )


    sessions=(

        Interaction.objects

        .values(
            "session_id"
        )

        .annotate(
            count=Count("id")
        )

    )


    total_events=sum(
        s["count"]
        for s in sessions
    )


    print(
        "Average events/session:",
        round(
            total_events /
            sessions.count(),
            3
        )
    )


    print(
        "Max events/session:",
        sessions.order_by(
            "-count"
        ).first()
    )


    print(
        "Sessions >=3 events:",
        sessions.filter(
            count__gte=3
        ).count()
    )


    purchase_sessions=(

        Interaction.objects

        .filter(
            event="purchase"
        )

        .values(
            "session_id"
        )

        .distinct()

        .count()

    )


    print(
        "Purchase sessions:",
        purchase_sessions
    )



# ==========================
# 7. Top Products
# ==========================


def product_test():

    section(
        "TOP PRODUCTS"
    )


    data=(

        Interaction.objects

        .values(
            "product__name"
        )

        .annotate(
            count=Count("id")
        )

        .order_by(
            "-count"
        )

        [:20]

    )


    for item in data:

        print(item)



# ==========================
# 8. Category Behavior
# ==========================


def category_test():

    section(
        "CATEGORY BEHAVIOR"
    )


    data=(

        Interaction.objects

        .values(
            "product__category__name"
        )

        .annotate(

            users=Count(
                "user_id",
                distinct=True
            ),

            interactions=Count(
                "id"
            )

        )

        .order_by(
            "-interactions"
        )

        [:20]

    )


    for item in data:

        print(item)



# ==========================
# 9. Dwell Time
# ==========================


def dwell_test():

    section(
        "DWELL TIME"
    )


    data=(

        Interaction.objects

        .values(
            "event"
        )

        .annotate(

            avg=Avg(
                "dwell_time"
            ),

            max=Max(
                "dwell_time"
            ),

            min=Min(
                "dwell_time"
            )

        )

    )


    for item in data:

        print(item)



# ==========================
# 10. User Activity
# ==========================


def user_test():

    section(
        "TOP USERS"
    )


    data=(

        Interaction.objects

        .values(
            "user_id"
        )

        .annotate(
            count=Count("id")
        )

        .order_by(
            "-count"
        )

        [:20]

    )


    for item in data:

        print(item)



# ==========================
# 11. Time Distribution
# ==========================


def time_test():

    section(
        "MONTH DISTRIBUTION"
    )


    data=(

        Interaction.objects

        .annotate(
            month=TruncMonth(
                "timestamp"
            )
        )

        .values(
            "month"
        )

        .annotate(
            count=Count("id")
        )

        .order_by(
            "month"
        )

    )


    for item in data:

        print(item)



# ==========================
# 12. Event Sequence Sample
# ==========================


def sample_session():

    section(
        "SESSION SAMPLE"
    )


    session=(

        Interaction.objects

        .values(
            "session_id"
        )

        .annotate(
            count=Count("id")
        )

        .order_by(
            "-count"
        )

        .first()

    )


    print(session)


    if session:


        events=(

            Interaction.objects

            .filter(
                session_id=session["session_id"]
            )

            .values(

                "event",
                "source",
                "product__name",
                "timestamp"

            )

            .order_by(
                "timestamp"
            )

        )


        for e in events:

            print(e)



# ==========================
# MAIN
# ==========================


def main():


    coverage_test()

    event_test()

    source_test()

    search_test()

    conversion_test()

    session_test()

    product_test()

    category_test()

    dwell_test()

    user_test()

    time_test()

    sample_session()



    section(
        "DONE"
    )



if __name__ == "__main__":

    main()