import re

STOP_WORDS = {
    "خوب",
    "بهترین",
    "ارزان",
    "قیمت",
    "جدید",
    "اصل",
    "اورجینال",
    "برای",
    "مدل",
}

REPLACE_MAP = {
    "ي": "ی",
    "ك": "ک",
    "‌": " ",   # نیم‌فاصله
}


def normalize_query(query: str) -> str:

    query = query.strip().lower()

    for old, new in REPLACE_MAP.items():
        query = query.replace(old, new)

    query = re.sub(r"\s+", " ", query)

    return query


def tokenize(query: str):

    query = normalize_query(query)

    return [
        word
        for word in query.split()
        if word not in STOP_WORDS
    ]


from shop.models import Brand, Category


BRANDS = {
    b.name.lower(): b
    for b in Brand.objects.all()
}

BRAND_ALIASES = {
    # موبایل
    "سامسونگ": "samsung",
    "اپل": "apple",
    "ایفون": "apple",
    "آیفون": "apple",
    "شیائومی": "xiaomi",
    "ردمی": "xiaomi",
    "هواوی": "huawei",
    "آنر": "honor",
    "اوپو": "oppo",
    "وان پلاس": "oneplus",
    "نوکیا": "nokia",
    "ویوو": "vivo",
    "گوگل": "google",

    # لپ تاپ و سخت افزار
    "ایسوس": "asus",
    "لنوو": "lenovo",
    "ایسر": "acer",
    "دل": "dell",
    "اچ پی": "hp",
    "ام اس آی": "msi",
    "گیگابایت": "gigabyte",
    "مایکروسافت": "microsoft",
    "اپل مک": "apple mac",

    # قطعات
    "اینتل": "intel",
    "ای ام دی": "amd",
    "کورسیر": "corsair",
    "کولر مستر": "cooler master",
    "کینگستون": "kingston",
    "سیگیت": "seagate",
    "وسترن دیجیتال": "western digital",
    "سن دیسک": "sandisk",

    # شبکه
    "تی پی لینک": "tp-link",
    "دی لینک": "d-link",
    "سیسکو": "cisco",
    "میکروتیک": "mikrotik",
    "یوبیکویتی": "ubiquiti",

    # لوازم جانبی
    "لاجیتک": "logitech",
    "انکر": "anker",
    "باسئوس": "baseus",
    "ریزر": "razer",
    "هایپر ایکس": "hyperx",
    "استیل سریز": "steelseries",

    # صوتی
    "جی بی ال": "jbl",
    "سونی": "sony",
    "بوز": "bose",
    "مارشال": "marshall",
    "فیلیپس": "philips",

    # دوربین
    "کانن": "canon",
    "نیکون": "nikon",
    "فوجی": "fujifilm",
    "گوپرو": "gopro",
    "دی جی آی": "dji",

    # کنسول
    "پلی استیشن": "playstation",
    "ایکس باکس": "xbox",
    "نینتندو": "nintendo",
    "والو": "valve",
    "متا کوئست": "meta quest",

    # پوشاک
    "نایک": "nike",
    "آدیداس": "adidas",
    "پوما": "puma",
    "ریباک": "reebok",
    "نیو بالانس": "new balance",
    "سالومون": "salomon",
    "ونس": "vans",
    "کانورس": "converse",
    "کراکس": "crocs",
    "اسکیچرز": "skechers",
    "اچ اند ام": "h&m",
    "زارا": "zara",
    "ال سی وایکیکی": "lc waikiki",
    "لیفایز": "levi's",
    "تامی هیلفیگر": "tommy hilfiger",
    "کلوین کلاین": "calvin klein",
    "گوچی": "gucci",

    # ساعت
    "رولکس": "rolex",
    "امگا": "omega",
    "تیسوت": "tissot",
    "کاسیو": "casio",
    "سیتیزن": "citizen",
    "سیکو": "seiko",
    "فسیل": "fossil",
    "دنیل ولینگتون": "daniel wellington",

    # عطر
    "دیور": "dior",
    "کرید": "creed",
    "شنل": "chanel",
    "ورساچه": "versace",
    "تام فورد": "tom ford",
    "ایو سن لوران": "ysl",
    "آرمانی": "armani",
    "هوگو باس": "hugo boss",
    "پاکو رابان": "paco rabanne",

    # آرایشی
    "لورآل": "l'oréal",
    "میبلین": "maybelline",
    "مک": "mac",
    "نیوا": "nivea",
    "داو": "dove",
    "ویشی": "vichy",
    "بایودرما": "bioderma",

    # لوازم خانگی
    "ال جی": "lg",
    "پاناسونیک": "panasonic",
    "بوش": "bosch",
    "هایر": "haier",
    "مایدیا": "midea",
    "بکو": "beko",
    "الکترولوکس": "electrolux",
    "ویرپول": "whirlpool",

    # خودرو
    "کاسترول": "castrol",
    "شل": "shell",
    "موبیل": "mobil",
    "والئو": "valeo",

    # حیوانات
    "رویال کنین": "royal canin",
    "جوسرا": "josera",
    "رفلکس": "reflex",
    "هپی کت": "happy cat",
    "هپی داگ": "happy dog",

    # باغبانی
    "گاردنا": "gardena",
    "ولف گارتن": "wolf garten",
}


CATEGORIES = list(
    Category.objects.values(
        "id",
        "name"
    )
)


def detect_brand(query):

    q = query.lower()

    # فارسی
    for fa, en in BRAND_ALIASES.items():

        if fa in q:

            return BRANDS.get(en)

    # انگلیسی
    for en, obj in BRANDS.items():

        if en in q:

            return obj

    return None


from django.db.models import Q, Case, When, Value, IntegerField

from shop.models import Product, Category


def detect_category(query):

    q = normalize_query(query)

    categories = Category.objects.all()

    # اول طولانی‌ترین اسم‌ها بررسی بشن
    categories = sorted(
        categories,
        key=lambda c: len(c.name),
        reverse=True
    )

    for category in categories:

        if category.name.lower() in q:

            return category

    return None


def search_products(query):

    query = normalize_query(query)

    if not query:
        return Product.objects.none()

    words = tokenize(query)

    qs = Product.objects.select_related(
        "brand",
        "category"
    )

    # برند
    brand = detect_brand(query)

    if brand:

        qs = qs.filter(
            brand=brand
        )

    # کتگوری
    category = detect_category(query)

    if category:

        qs = qs.filter(
            category=category
        )

    # حذف کلمات برند و کتگوری
    filtered_words = []

    for word in words:

        if brand and word in normalize_query(brand.name):
            continue

        if category and word in normalize_query(category.name):
            continue

        filtered_words.append(word)

    # جستجوی کلمات باقی‌مانده
    for word in filtered_words:

        qs = qs.filter(

            Q(name__icontains=word)

            |

            Q(description__icontains=word)

            |

            Q(features__value__icontains=word)

        )

    # Ranking
    qs = qs.annotate(

        score=Case(

            When(name__icontains=query, then=Value(100)),

            default=Value(0),

            output_field=IntegerField()

        )

    ).order_by(

        "-score",

        "-created"

    ).distinct()

    return qs


def normalize_search_tokens(words):

    normalized = []

    replacements = {
        "ترابایت": "tb",
        "گیگ": "gb",
        "گیگابایت": "gb",
        "مگابایت": "mb",
        "یک": "1",
        "دو": "2",
        "سه": "3",
        "چهار": "4",
        "پنج": "5",
        "شش": "6",
        "هفت": "7",
        "هشت": "8",
        "نه": "9",
        "ده": "10",
    }

    for word in words:

        normalized.append(
            replacements.get(word, word)
        )

    return normalized
