import os
import sys


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



from recommendation.ml.implicit_dataset import ImplicitDataset



dataset = ImplicitDataset()


matrix = dataset.build_matrix()