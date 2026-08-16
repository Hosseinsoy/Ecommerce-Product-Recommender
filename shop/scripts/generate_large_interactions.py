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


TEST_SEARCH_LIMIT = 40000


DIRECT_SESSION_COUNT = 20000



VIEW_TO_WISHLIST = 0.08


VIEW_TO_CART = 0.05


CART_TO_PURCHASE = 0.30



DWELL_MIN = 20


DWELL_MAX = 300



# ==========================
# Users
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

    if random.random() < 0.25:

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



def random_time():

    return (

        timezone.now()

        -
        timedelta(

            days=random.randint(
                1,
                365
            ),

            minutes=random.randint(
                0,
                1440
            )

        )

    )



def get_metadata(product):

    return {

        "category":

            product.category.name
            if product.category
            else None,


        "brand":

            product.brand.name
            if product.brand
            else None,


        "price":

            product.price

    }




def create_interaction(

        user,

        product,

        event,

        source,

        session_id,

        search_query=None,

        timestamp=None,

        dwell_time=0

):


    return Interaction(

        user=user,

        product=product,

        event=event,

        source=source,

        session_id=session_id,

        search_query=search_query,

        timestamp=
        timestamp
        or random_time(),

        dwell_time=dwell_time,

        metadata=get_metadata(
            product
        )

    )



# ==========================
# Search Sessions
# ==========================


def generate_search_sessions():


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


        start_time = random_time()



        products = list(

            Product.objects.filter(

                Q(
                    name__icontains=query.query
                )

                |

                Q(
                    description__icontains=query.query
                )

                |

                Q(
                    brand__name__icontains=query.query
                )

                |

                Q(
                    category__name__icontains=query.query
                )

            )

            .distinct()

            [:15]

        )


        if not products:

            continue



        selected_products = random.sample(

            products,

            random.randint(
                1,
                min(
                    5,
                    len(products)
                )
            )

        )



        current_time = start_time



        for idx, product in enumerate(
            selected_products
        ):


            current_time += timedelta(

                minutes=random.randint(
                    1,
                    7
                )

            )


            # وضعیت محصول در session

            state = "view"



            # اولین بازدید از سرچ

            if idx == 0:

                source = "search"

                search_query = query


            else:

                source = "direct"

                search_query = None



            interactions.append(

                create_interaction(

                    user=user,

                    product=product,

                    event="view",

                    source=source,

                    session_id=session_id,

                    search_query=search_query,

                    timestamp=current_time,

                    dwell_time=random.randint(
                        DWELL_MIN,
                        DWELL_MAX
                    )

                )

            )



            state = "view"
            # wishlist

            if random.random() < VIEW_TO_WISHLIST:


                current_time += timedelta(
                    minutes=random.randint(
                        1,
                        3
                    )
                )


                interactions.append(

                    create_interaction(

                        user=user,

                        product=product,

                        event="wishlist",

                        source=source,

                        session_id=session_id,

                        timestamp=current_time

                    )

                )


                state = "wishlist"



            # cart

            if random.random() < VIEW_TO_CART:


                current_time += timedelta(

                    minutes=random.randint(
                        2,
                        5
                    )

                )


                interactions.append(

                    create_interaction(

                        user=user,

                        product=product,

                        event="cart",

                        source="direct",

                        session_id=session_id,

                        timestamp=current_time

                    )

                )


                state = "cart"



                # purchase

                if random.random() < CART_TO_PURCHASE:


                    current_time += timedelta(

                        minutes=random.randint(
                            10,
                            60
                        )

                    )


                    interactions.append(

                        create_interaction(

                            user=user,

                            product=product,

                            event="purchase",

                            source="direct",

                            session_id=session_id,

                            timestamp=current_time

                        )

                    )


                    state = "purchase"





        if index % 1000 == 0:

            print(
                f"{index} search processed"
            )




    Interaction.objects.bulk_create(

        interactions,

        batch_size=2000

    )


    print(
        "Search interactions:",
        len(interactions)
    )



# ==========================
# Direct Sessions
# ==========================


def generate_direct_sessions():


    print(
        "Generating direct sessions..."
    )


    products = list(

        Product.objects.all()

    )


    interactions=[]



    for i in range(

        DIRECT_SESSION_COUNT

    ):


        user = choose_user()


        session_id = create_session_id()


        start_time = random_time()


        source = random.choice(

            [

                "direct",

                "home",

                "category"

            ]

        )



        product = random.choice(

            products

        )



        current_time = start_time



        interactions.append(

            create_interaction(

                user=user,

                product=product,

                event="view",

                source=source,

                session_id=session_id,

                timestamp=current_time,

                dwell_time=random.randint(

                    DWELL_MIN,

                    DWELL_MAX

                )

            )

        )



        # wishlist

        if random.random() < VIEW_TO_WISHLIST:


            current_time += timedelta(

                minutes=2

            )


            interactions.append(

                create_interaction(

                    user=user,

                    product=product,

                    event="wishlist",

                    source=source,

                    session_id=session_id,

                    timestamp=current_time

                )

            )



        # cart

        if random.random() < VIEW_TO_CART:


            current_time += timedelta(

                minutes=5

            )


            interactions.append(

                create_interaction(

                    user=user,

                    product=product,

                    event="cart",

                    source="direct",

                    session_id=session_id,

                    timestamp=current_time

                )

            )



            # purchase

            if random.random() < CART_TO_PURCHASE:


                current_time += timedelta(

                    minutes=random.randint(

                        10,

                        60

                    )

                )


                interactions.append(

                    create_interaction(

                        user=user,

                        product=product,

                        event="purchase",

                        source="direct",

                        session_id=session_id,

                        timestamp=current_time

                    )

                )



        if i % 5000 == 0:

            print(

                f"{i} direct sessions processed"

            )



    Interaction.objects.bulk_create(

        interactions,

        batch_size=2000

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


    generate_search_sessions()


    generate_direct_sessions()


    print(
        "===================="
    )


    print(
        "ALL DONE"
    )



if __name__ == "__main__":

    main()