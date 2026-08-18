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



# ==========================
# Imports
# ==========================

from shop.models import Interaction as OldInteraction

from recommendation.models import (
    RecommendationInteraction
)



# ==========================
# Migration
# ==========================


def migrate_interactions():


    print(
        "Starting migration..."
    )



    old_interactions = (
        OldInteraction.objects
        .all()
        .select_related(
            "user",
            "product",
            "search_query"
        )
    )



    total = old_interactions.count()


    print(
        "Old interactions:",
        total
    )



    new_objects = []



    for index, interaction in enumerate(
        old_interactions,
        start=1
    ):


        new_objects.append(

            RecommendationInteraction(

                user=interaction.user,

                product=interaction.product,

                session_id=interaction.session_id,

                event=interaction.event,

                source=interaction.source,

                search_query=interaction.search_query,

                timestamp=interaction.timestamp,

                dwell_time=interaction.dwell_time

            )

        )



        # هر 1000 رکورد ذخیره شود
        if len(new_objects) >= 1000:


            RecommendationInteraction.objects.bulk_create(
                new_objects,
                batch_size=1000
            )


            new_objects.clear()



            print(
                f"{index}/{total} migrated"
            )



    # باقی مانده‌ها

    if new_objects:

        RecommendationInteraction.objects.bulk_create(
            new_objects,
            batch_size=1000
        )



    print(
        "Migration completed!"
    )



    print(
        "New interactions:",
        RecommendationInteraction.objects.count()
    )





if __name__ == "__main__":

    migrate_interactions()