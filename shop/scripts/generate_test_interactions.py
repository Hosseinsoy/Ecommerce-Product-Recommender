import os
import sys
import random
import uuid

from datetime import timedelta


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


from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import get_user_model


User = get_user_model()


from shop.models import (
    Product,
    Interaction,
    SearchQuery
)



# ==========================
# Settings
# ==========================

TEST_SEARCH_LIMIT = 1000

DIRECT_INTERACTION_COUNT = 5000


VIEW_TO_WISHLIST_PROB = 0.08

VIEW_TO_CART_PROB = 0.04

CART_TO_PURCHASE_PROB = 0.25


DWELL_MIN = 20

DWELL_MAX = 300



# ==========================
# User Distribution
# ==========================


all_users = list(
    User.objects.all()
)


if not all_users:

    raise Exception(
        "No users found"
    )



active_count = max(
    1,
    int(
        len(all_users) * 0.2
    )
)



active_users = random.sample(
    all_users,
    active_count
)



active_ids = {
    u.id
    for u in active_users
}



normal_users = [

    u

    for u in all_users

    if u.id not in active_ids

]



def choose_user():

    if random.random() < 0.2:

        return random.choice(
            active_users
        )

    return random.choice(
        normal_users
    )



# ==========================
# Helpers
# ==========================


def create_session_id():

    return uuid.uuid4()



def generate_session_time():

    return (
        timezone.now()
        -
        timedelta(
            days=random.randint(
                1,
                120
            ),
            minutes=random.randint(
                0,
                1440
            )
        )
    )



def create_interaction(
        user,
        product,
        event,
        source,
        session_id,
        search_query=None,
        dwell_time=0,
        timestamp=None
):


    return Interaction(

        user=user,

        product=product,

        session_id=session_id,

        source=source,

        search_query=search_query,

        event=event,

        timestamp=timestamp
        or generate_session_time(),

        dwell_time=dwell_time

    )



# ==========================
# Search Sessions
# ==========================


def generate_search_interactions():


    print(
        "Generating search sessions..."
    )


    queries = list(

        SearchQuery.objects
        .select_related(
            "user"
        )
        .order_by(
            "id"
        )
        [:TEST_SEARCH_LIMIT]

    )


    interactions=[]



    for index, query in enumerate(
        queries,
        start=1
    ):



        user = (

            query.user

            if query.user

            else choose_user()

        )



        session_id = create_session_id()



        start_time = generate_session_time()



        products = list(

            Product.objects.filter(

                Q(name__icontains=query.query)

                |

                Q(description__icontains=query.query)

                |

                Q(brand__name__icontains=query.query)

                |

                Q(category__name__icontains=query.query)

            )
            .distinct()
            [:10]

        )



        if not products:

            continue



        selected_products = random.sample(

            products,

            min(
                len(products),
                random.randint(
                    2,
                    5
                )
            )

        )



        current_time = start_time



        for product in selected_products:



            current_time += timedelta(

                minutes=random.randint(
                    1,
                    5
                )

            )



            # همه رفتارهای این session از سرچ آمده‌اند

            source = "search"

            sq = query



            # VIEW

            interactions.append(

                create_interaction(

                    user=user,

                    product=product,

                    event="view",

                    source=source,

                    session_id=session_id,

                    search_query=sq,

                    dwell_time=random.randint(

                        DWELL_MIN,

                        DWELL_MAX

                    ),

                    timestamp=current_time

                )

            )



            # Wishlist

            if random.random() < VIEW_TO_WISHLIST_PROB:


                interactions.append(

                    create_interaction(

                        user=user,

                        product=product,

                        event="wishlist",

                        source=source,

                        session_id=session_id,

                        search_query=sq,

                        timestamp=current_time + timedelta(
                            minutes=3
                        )

                    )

                )



            # Cart

            if random.random() < VIEW_TO_CART_PROB:


                cart_time = (

                    current_time

                    +

                    timedelta(
                        minutes=5
                    )

                )



                interactions.append(

                    create_interaction(

                        user=user,

                        product=product,

                        event="cart",

                        source=source,

                        session_id=session_id,

                        search_query=sq,

                        timestamp=cart_time

                    )

                )



                # Purchase

                if random.random() < CART_TO_PURCHASE_PROB:


                    interactions.append(

                        create_interaction(

                            user=user,

                            product=product,

                            event="purchase",

                            source=source,

                            session_id=session_id,

                            search_query=sq,

                            timestamp=

                            cart_time

                            +

                            timedelta(

                                minutes=random.randint(
                                    10,
                                    60
                                )

                            )

                        )

                    )



        if index % 100 == 0:


            print(

                f"{index} searches processed"

            )



    Interaction.objects.bulk_create(

        interactions,

        batch_size=1000

    )



    print(

        "Search interactions:",

        len(interactions)

    )



# ==========================
# Direct Sessions
# ==========================


def generate_direct_interactions():


    print(
        "Generating direct sessions..."
    )



    products = list(
        Product.objects.all()
    )



    interactions=[]



    for _ in range(
        DIRECT_INTERACTION_COUNT
    ):



        user = choose_user()



        product=random.choice(
            products
        )



        session_id=create_session_id()



        start_time=generate_session_time()



        source=random.choice(

            [
                "direct",
                "category",
                "home"
            ]

        )



        interactions.append(

            create_interaction(

                user=user,

                product=product,

                event="view",

                source=source,

                session_id=session_id,

                dwell_time=random.randint(

                    DWELL_MIN,

                    DWELL_MAX

                ),

                timestamp=start_time

            )

        )



        if random.random() < VIEW_TO_WISHLIST_PROB:


            interactions.append(

                create_interaction(

                    user=user,

                    product=product,

                    event="wishlist",

                    source=source,

                    session_id=session_id,

                    timestamp=start_time + timedelta(
                        minutes=3
                    )

                )

            )



        if random.random() < VIEW_TO_CART_PROB:


            cart_time = start_time + timedelta(
                minutes=5
            )



            interactions.append(

                create_interaction(

                    user=user,

                    product=product,

                    event="cart",

                    source=source,

                    session_id=session_id,

                    timestamp=cart_time

                )

            )



            if random.random() < CART_TO_PURCHASE_PROB:


                interactions.append(

                    create_interaction(

                        user=user,

                        product=product,

                        event="purchase",

                        source=source,

                        session_id=session_id,

                        timestamp=

                        cart_time

                        +

                        timedelta(

                            minutes=random.randint(
                                10,
                                60
                            )

                        )

                    )

                )



    Interaction.objects.bulk_create(

        interactions,

        batch_size=1000

    )



    print(

        "Direct interactions:",

        len(interactions)

    )



# ==========================
# Main
# ==========================


def main():


    print(
        "START GENERATING..."
    )


    generate_search_interactions()


    generate_direct_interactions()


    print(
        "ALL DONE"
    )



main()