import os
import sys
import django
import pandas as pd


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

from recommendation.models import Interaction



# ==========================
# Export Dataset
# ==========================

print("==============================")
print("Exporting implicit dataset...")
print("==============================")


interactions = Interaction.objects.select_related(
    "user",
    "product",
    "search_query"
).all()



data = []



for interaction in interactions:


    product = interaction.product


    row = {


        "user_id": interaction.user_id,


        "product_id": interaction.product_id,


        "product_name": product.name,


        "event": interaction.event,


        "interaction_score": interaction.interaction_score,


        "source": interaction.source,


        "search_query": (

            interaction.search_query.query

            if interaction.search_query

            else None

        ),


        "dwell_time": interaction.dwell_time,


        "timestamp": interaction.timestamp,


        "metadata": interaction.metadata,


    }


    data.append(row)



df = pd.DataFrame(data)



output_path = os.path.join(

    BASE_DIR,

    "implicit_dataset.csv"

)



df.to_csv(

    output_path,

    index=False,

    encoding="utf-8-sig"

)



print("==============================")
print(
    "Dataset exported successfully"
)

print(
    "Rows:",
    len(df)
)

print(
    "Path:",
    output_path
)

print("==============================")