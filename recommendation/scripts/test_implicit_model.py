import os
import sys
import django
import pickle


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


from recommendation.ml.implicit_dataset import ImplicitDataset
from recommendation.ml.implicit_model import ImplicitALSModel



MODEL_DIR = os.path.join(
    BASE_DIR,
    "recommendation",
    "ml",
    "models"
)


os.makedirs(
    MODEL_DIR,
    exist_ok=True
)



dataset = ImplicitDataset()


matrix = dataset.build_matrix()



# save mappings

with open(
    os.path.join(MODEL_DIR, "user_mapping.pkl"),
    "wb"
) as f:
    pickle.dump(
        dataset.user_mapping,
        f
    )



with open(
    os.path.join(MODEL_DIR, "reverse_user_mapping.pkl"),
    "wb"
) as f:
    pickle.dump(
        dataset.reverse_user_mapping,
        f
    )



with open(
    os.path.join(MODEL_DIR, "item_mapping.pkl"),
    "wb"
) as f:
    pickle.dump(
        dataset.item_mapping,
        f
    )



with open(
    os.path.join(MODEL_DIR, "reverse_item_mapping.pkl"),
    "wb"
) as f:
    pickle.dump(
        dataset.reverse_item_mapping,
        f
    )



print("Mappings saved")



model = ImplicitALSModel()


model.train(
    matrix
)

print("MODEL USERS:", model.model.user_factors.shape)
print("MODEL ITEMS:", model.model.item_factors.shape)
print("MATRIX:", matrix.shape)

model.save(
    os.path.join(
        MODEL_DIR,
        "als_model.pkl"
    )
)