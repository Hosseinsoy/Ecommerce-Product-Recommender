import pandas as pd

FILE = r"C:\Users\Aliba\Downloads\archive\events.csv"

print("Reading Retailrocket events...")

# خواندن فایل
df = pd.read_csv(FILE)

print("\n===== GENERAL =====")
print(f"Total events     : {len(df):,}")
print(f"Unique visitors  : {df['visitorid'].nunique():,}")
print(f"Unique items      : {df['itemid'].nunique():,}")

print("\n===== EVENT TYPES =====")
event_counts = df["event"].value_counts()
print(event_counts)

event_percent = (
    event_counts / len(df) * 100
).round(2)

print("\nPercentage:")
print(event_percent)

print("\n===== USER ACTIVITY =====")

user_events = df.groupby("visitorid").size()

print(user_events.describe())

print("\nUsers by activity level:")

low = (user_events <= 10).sum()
medium = ((user_events > 10) & (user_events <= 30)).sum()
high = (user_events > 30).sum()

print(f"Low    : {low:,}")
print(f"Medium : {medium:,}")
print(f"High   : {high:,}")

print("\n===== PRODUCT POPULARITY =====")

popular = (
    df.groupby("itemid")
      .size()
      .sort_values(ascending=False)
      .head(20)
)

print(popular)

print("\n===== PURCHASE CONVERSION =====")

views = (
    df[df.event == "view"]
      .groupby("visitorid")
      .size()
)

cart = (
    df[df.event == "addtocart"]
      .groupby("visitorid")
      .size()
)

purchase = (
    df[df.event == "transaction"]
      .groupby("visitorid")
      .size()
)

summary = pd.DataFrame({
    "views": views,
    "cart": cart,
    "purchase": purchase
}).fillna(0)

print(summary.describe())

print("\n===== TIME RANGE =====")

df["datetime"] = pd.to_datetime(
    df["timestamp"],
    unit="ms"
)

print(df["datetime"].min())
print(df["datetime"].max())

print("\nDone.")