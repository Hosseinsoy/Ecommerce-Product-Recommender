import pandas as pd
from tqdm import tqdm

FILE = r"C:\Users\Aliba\Downloads\archive\events.csv"

print("Reading events.csv ...")

df = pd.read_csv(
    FILE,
    usecols=["visitorid", "itemid", "event", "timestamp"]
)

# تبدیل زمان
df["datetime"] = pd.to_datetime(
    df["timestamp"],
    unit="ms"
)

# مرتب‌سازی
df = df.sort_values(
    ["visitorid", "datetime"]
)

print("\n===== BASIC =====")
print(f"Events    : {len(df):,}")
print(f"Visitors  : {df.visitorid.nunique():,}")

# -----------------------------
# ساعات پرترافیک
# -----------------------------

print("\n===== HOURLY ACTIVITY =====")

hourly = (
    df.groupby(
        df["datetime"].dt.hour
    )
    .size()
    .sort_index()
)

print(hourly)

# -----------------------------
# روزهای هفته
# -----------------------------

print("\n===== WEEKDAY ACTIVITY =====")

weekday = (
    df.groupby(
        df["datetime"].dt.day_name()
    )
    .size()
)

print(weekday)

# -----------------------------
# Sessionها
# 30 دقیقه فاصله = Session جدید
# -----------------------------

print("\n===== SESSION STATS =====")

session_lengths = []

for _, group in tqdm(
    df.groupby("visitorid"),
    total=df["visitorid"].nunique()
):

    times = group["datetime"]

    gaps = times.diff()

    session_id = (
        gaps > pd.Timedelta(minutes=30)
    ).cumsum()

    lengths = session_id.value_counts()

    session_lengths.extend(
        lengths.tolist()
    )

session_series = pd.Series(session_lengths)

print(session_series.describe())

# -----------------------------
# View -> Cart
# -----------------------------

print("\n===== VIEW -> CART =====")

view_to_cart = []

for _, group in tqdm(
    df.groupby("visitorid"),
    total=df["visitorid"].nunique()
):

    group = group.sort_values("datetime")

    for item, events in group.groupby("itemid"):

        view = events[
            events.event == "view"
        ]

        cart = events[
            events.event == "addtocart"
        ]

        if not view.empty and not cart.empty:

            delta = (
                cart.iloc[0]["datetime"]
                -
                view.iloc[0]["datetime"]
            ).total_seconds()

            if delta >= 0:
                view_to_cart.append(delta)

v2c = pd.Series(view_to_cart)

print(v2c.describe())

# -----------------------------
# Cart -> Purchase
# -----------------------------

print("\n===== CART -> PURCHASE =====")

cart_to_purchase = []

for _, group in tqdm(
    df.groupby("visitorid"),
    total=df["visitorid"].nunique()
):

    group = group.sort_values("datetime")

    for item, events in group.groupby("itemid"):

        cart = events[
            events.event == "addtocart"
        ]

        purchase = events[
            events.event == "transaction"
        ]

        if not cart.empty and not purchase.empty:

            delta = (
                purchase.iloc[0]["datetime"]
                -
                cart.iloc[0]["datetime"]
            ).total_seconds()

            if delta >= 0:
                cart_to_purchase.append(delta)

c2p = pd.Series(cart_to_purchase)

print(c2p.describe())

# -----------------------------
# Dwell Time پیشنهادی
# -----------------------------

print("\n===== VIEW DWELL PROPOSAL =====")

view_counts = (
    df[df.event == "view"]
    .groupby("visitorid")
    .size()
)

print(view_counts.describe())

print("\nDone.")