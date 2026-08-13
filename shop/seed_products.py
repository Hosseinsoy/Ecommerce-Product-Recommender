from django.utils.text import slugify
from django.db import transaction
from decimal import Decimal
import random

from shop.models import (
    Product,
    ProductFeature,
    ProductVariant,
    ProductSizeVariant,
    ProductColorVariant,
    Category,
    Brand, ProductSeller
)

from account.models import ShopSeller


# ----------------------------------------
# ایجاد فروشنده پیش فرض
# ----------------------------------------

def get_default_seller():

    seller, created = ShopSeller.objects.get_or_create(
        phone="09120000000",
        defaults={
            "first_name": "Blue",
            "last_name": "Shop",
            "shop_name": "BlueShop",
            "shop_phone": "09120000000",
            "shop_address": "Online Store",
            "email": "info@blueshop.com",
            "shop_email": "info@blueshop.com",
            "is_active": True,
            "is_staff": False,
        }
    )

    return seller



# ----------------------------------------
# توابع کمکی
# ----------------------------------------

def create_feature(product, features):

    """
    ساخت ویژگی های محصول

    مثال:
    {
        "RAM":"16GB",
        "CPU":"Core i7",
    }
    """

    for key, value in features.items():

        ProductFeature.objects.create(
            product=product,
            name=key,
            value=value
        )



def create_variants(product, colors=None, sizes=None):

    """
    ایجاد رنگ و سایز فقط برای محصولاتی که نیاز دارند
    """

    if colors:

        product.has_color_option = True

        for color in colors:

            ProductColorVariant.objects.create(
                product=product,
                color=color
            )


    if sizes:

        product.has_size_option = True

        for size in sizes:

            ProductSizeVariant.objects.create(
                product=product,
                size=size
            )


    product.save()



def create_product_seller(product, seller):

    """
    ایجاد فروشنده برای محصول
    """

    ProductSeller.objects.create(
        product=product,
        seller=seller,
        price=product.off_price if product.off > 0 else product.price,
        inventory=random.randint(5, 100),
        warranty="گارانتی معتبر شرکتی",
        satisfaction=random.randint(80, 100),
        performance="عالی",
        shipping_type="ارسال شاپیک",
    )



# ----------------------------------------
# ساخت محصول
# ----------------------------------------

def create_product(
        name,
        category_name,
        brand_name,
        description,
        price,
        features,
        colors=None,
        sizes=None
):

    try:

        category = Category.objects.get(
            name=category_name
        )

    except Category.DoesNotExist:

        print(
            f"Category not found: {category_name}"
        )
        return None



    try:

        brand = Brand.objects.get(
            name=brand_name
        )

    except Brand.DoesNotExist:

        print(
            f"Brand not found: {brand_name}"
        )
        return None

    # جلوگیری از تکراری بودن slug

    base_slug = slugify(name)

    slug = base_slug

    counter = 1

    while Product.objects.filter(slug=slug).exists():
        counter += 1

        slug = f"{base_slug}-{counter}"


    price = int(price)

    off = random.choice(
        [
            0,
            5,
            10,
            15,
            20,
            25
        ]
    )


    off_price = price - (
        price * off // 100
    )



    product = Product.objects.create(

        category=category,

        brand=brand,

        name=name,

        description=description,

        inventory=random.randint(
            5,
            200
        ),

        is_available=True,

        weight=random.randint(
            100,
            5000
        ),

        price=price,

        off=off,

        off_price=off_price,

        slug=slug,
    )



    create_feature(
        product,
        features
    )


    create_variants(
        product,
        colors,
        sizes
    )


    seller = get_default_seller()


    create_product_seller(
        product,
        seller
    )


    print(
        f"Created: {product.name}"
    )


    return product



# ----------------------------------------
# شروع تراکنش اصلی
# ----------------------------------------

@transaction.atomic
def run_seed():

    print(
        "Starting product generation..."
    )


    count_before = Product.objects.count()

    # اینجا محصولات هر بخش رو اضافه میکنیم
    create_product(
        name="کوله پشتی Lenovo Urban Backpack",
        category_name="کیف و کوله پشتی",
        brand_name="Lenovo",
        description="""
        کوله پشتی Lenovo Urban یک کیف سبک و کاربردی
        برای لپ تاپ، دانشگاه و استفاده روزمره است.
        """,
        price=2800000,
        features={
            "محفظه لپ تاپ": "15.6 اینچ",
            "جنس": "Polyester",
            "ضدآب": "مقاوم",
            "کاربرد": "روزمره",
            "وزن": "سبک"
        },
        colors=["مشکی", "خاکستری"]
    )

    create_product(
        name="کوله پشتی Dell Essential Backpack",
        category_name="کیف و کوله پشتی",
        brand_name="Dell",
        description="""
        Dell Essential Backpack برای حمل لپ تاپ و لوازم جانبی
        با طراحی ساده و مقاوم ساخته شده است.
        """,
        price=2500000,
        features={
            "محفظه لپ تاپ": "15.6 اینچ",
            "جنس": "Nylon",
            "تعداد جیب": "چند بخش",
            "کاربرد": "اداری",
            "بند": "پددار"
        },
        colors=["مشکی"]
    )

    create_product(
        name="کوله پشتی لپ تاپ Asus Nereus",
        category_name="کیف و کوله پشتی",
        brand_name="Asus",
        description="""
        Asus Nereus یک کوله اقتصادی برای کاربران لپ تاپ
        با فضای مناسب و طراحی مقاوم است.
        """,
        price=2200000,
        features={
            "محفظه لپ تاپ": "15.6 اینچ",
            "جنس": "Polyester",
            "وزن": "کم",
            "کاربرد": "دانشگاه",
            "ضدآب": "مقاوم"
        },
        colors=["مشکی"]
    )

    create_product(
        name="کوله پشتی Xiaomi Mi Casual Daypack",
        category_name="کیف و کوله پشتی",
        brand_name="Xiaomi",
        description="""
        Xiaomi Mi Casual Daypack یک کیف مینیمال
        برای حمل وسایل شخصی و تجهیزات روزانه است.
        """,
        price=1600000,
        features={
            "جنس": "Oxford Fabric",
            "ضدآب": "دارد",
            "کاربرد": "روزمره",
            "وزن": "سبک",
            "طراحی": "مینیمال"
        },
        colors=["مشکی", "آبی"]
    )

    create_product(
        name="کوله پشتی مسافرتی American Tourister At Work",
        category_name="کیف و کوله پشتی",
        brand_name="American Tourister",
        description="""
        کوله مسافرتی American Tourister At Work
        مناسب سفرهای کاری و استفاده طولانی مدت است.
        """,
        price=6500000,
        features={
            "محفظه لپ تاپ": "15.6 اینچ",
            "جنس": "Polyester",
            "کاربرد": "Travel",
            "بند": "ارگونومیک",
            "فضای داخلی": "زیاد"
        },
        colors=["مشکی", "سرمه‌ای"]
    )

    create_product(
        name="کیف دستی زنانه Armani Exchange",
        category_name="کیف و کوله پشتی",
        brand_name="Armani",
        description="""
        کیف دستی Armani با طراحی شیک و کیفیت ساخت بالا
        مناسب استایل رسمی و روزمره بانوان است.
        """,
        price=12000000,
        features={
            "جنس": "چرم مصنوعی با کیفیت",
            "نوع": "Hand Bag",
            "بند": "قابل تنظیم",
            "کاربرد": "رسمی",
            "طراحی": "کلاسیک"
        },
        colors=["مشکی", "کرم"]
    )

    create_product(
        name="کیف دوشی مردانه Hugo Boss",
        category_name="کیف و کوله پشتی",
        brand_name="Hugo Boss",
        description="""
        کیف دوشی مردانه Hugo Boss با طراحی رسمی
        برای حمل وسایل شخصی و استفاده کاری مناسب است.
        """,
        price=10000000,
        features={
            "جنس": "Synthetic Leather",
            "نوع": "دوشی",
            "بند": "بلند",
            "کاربرد": "رسمی",
            "محفظه": "چند بخش"
        },
        colors=["مشکی", "قهوه‌ای"]
    )

    create_product(
        name="کیف کمری Nike Heritage Waist Bag",
        category_name="کیف و کوله پشتی",
        brand_name="Nike",
        description="""
        کیف کمری Nike Heritage برای حمل وسایل کوچک
        هنگام ورزش و فعالیت‌های روزانه طراحی شده است.
        """,
        price=1800000,
        features={
            "جنس": "Polyester",
            "نوع": "کمری",
            "کاربرد": "ورزش و سفر",
            "بند": "قابل تنظیم",
            "تعداد جیب": "2 عدد"
        },
        colors=["مشکی", "سبز"]
    )

    create_product(
        name="کیف کمری Adidas Essentials Waist Bag",
        category_name="کیف و کوله پشتی",
        brand_name="Adidas",
        description="""
        کیف کمری Adidas Essentials یک کیف سبک
        برای استفاده روزمره و ورزشی است.
        """,
        price=1700000,
        features={
            "جنس": "Polyester",
            "نوع": "کمری",
            "ضدآب": "مقاوم",
            "وزن": "سبک",
            "کاربرد": "روزانه"
        },
        colors=["مشکی"]
    )

    create_product(
        name="کیف لپ تاپ Samsonite Classic Business",
        category_name="کیف و کوله پشتی",
        brand_name="Samsonite",
        description="""
        کیف لپ تاپ Samsonite Classic Business
        برای مدیران و کاربران حرفه‌ای طراحی شده است.
        """,
        price=9000000,
        features={
            "محفظه لپ تاپ": "15.6 اینچ",
            "جنس": "Polyester",
            "بند دوشی": "دارد",
            "محفظه اسناد": "دارد",
            "کاربرد": "Business"
        },
        colors=["مشکی"]
    )

    create_product(
        name="کیف لپ تاپ American Tourister Laptop Bag",
        category_name="کیف و کوله پشتی",
        brand_name="American Tourister",
        description="""
        کیف لپ تاپ American Tourister یک کیف سبک
        برای دانشجویان و کاربران اداری است.
        """,
        price=3200000,
        features={
            "محفظه لپ تاپ": "15.6 اینچ",
            "جنس": "Nylon",
            "بند": "قابل تنظیم",
            "وزن": "کم",
            "کاربرد": "روزمره"
        },
        colors=["مشکی"]
    )

    create_product(
        name="کیف ورزشی Puma Fundamentals Sports Bag",
        category_name="کیف و کوله پشتی",
        brand_name="Puma",
        description="""
        کیف ورزشی Puma Fundamentals برای باشگاه
        و حمل تجهیزات ورزشی طراحی شده است.
        """,
        price=3500000,
        features={
            "جنس": "Polyester",
            "محفظه کفش": "دارد",
            "نوع": "ساک ورزشی",
            "بند": "دو حالته",
            "ظرفیت": "متوسط"
        },
        colors=["مشکی", "طوسی"]
    )

    create_product(
        name="کیف ورزشی Reebok Training Bag",
        category_name="کیف و کوله پشتی",
        brand_name="Reebok",
        description="""
        کیف ورزشی Reebok مناسب تمرینات باشگاهی
        و حمل لباس و تجهیزات ورزشی است.
        """,
        price=3000000,
        features={
            "جنس": "Polyester",
            "کاربرد": "ورزش",
            "محفظه اصلی": "بزرگ",
            "بند": "قابل تنظیم",
            "مقاومت": "بالا"
        },
        colors=["مشکی", "آبی"]
    )

    create_product(
        name="کیف سفر Xiaomi Travel Bag",
        category_name="کیف و کوله پشتی",
        brand_name="Xiaomi",
        description="""
        کیف سفر Xiaomi برای حمل لباس و وسایل شخصی
        در سفرهای کوتاه طراحی شده است.
        """,
        price=2500000,
        features={
            "جنس": "Oxford",
            "نوع": "Travel Bag",
            "ضدآب": "مقاوم",
            "فضای داخلی": "زیاد",
            "وزن": "سبک"
        },
        colors=["مشکی", "خاکستری"]
    )

    create_product(
        name="کوله مدرسه کودک Lego Backpack",
        category_name="کیف و کوله پشتی",
        brand_name="LEGO",
        description="""
        کوله مدرسه Lego با طراحی کودکانه
        برای دانش‌آموزان و استفاده روزمره مناسب است.
        """,
        price=2800000,
        features={
            "جنس": "Polyester",
            "کاربرد": "مدرسه",
            "محفظه اصلی": "دارد",
            "وزن": "سبک",
            "طراحی": "کودکانه"
        },
        colors=["قرمز", "آبی"]
    )

    create_product(
        name="کوله کودک Fisher Price Kids Backpack",
        category_name="کیف و کوله پشتی",
        brand_name="Fisher Price",
        description="""
        کوله کودک Fisher Price با طراحی جذاب
        برای کودکان خردسال طراحی شده است.
        """,
        price=2000000,
        features={
            "جنس": "پارچه نرم",
            "کاربرد": "کودک",
            "وزن": "خیلی سبک",
            "طراحی": "کارتونی",
            "محفظه": "اصلی"
        },
        colors=["صورتی", "آبی"]
    )

    create_product(
        name="کیف چرمی مردانه نوین چرم",
        category_name="کیف و کوله پشتی",
        brand_name="نوین چرم",
        description="""
        کیف چرمی مردانه نوین چرم مناسب استفاده رسمی
        با طراحی شیک و دوام بالا است.
        """,
        price=7000000,
        features={
            "جنس": "چرم طبیعی",
            "نوع": "دستی",
            "کاربرد": "رسمی",
            "محفظه": "چند بخش",
            "دوخت": "مقاوم"
        },
        colors=["مشکی", "قهوه‌ای"]
    )

    create_product(
        name="کوله پشتی ورزشی Decathlon",
        category_name="کیف و کوله پشتی",
        brand_name="Decathlon",
        description="""
        کوله پشتی Decathlon برای ورزش، کوهنوردی
        و فعالیت‌های فضای باز طراحی شده است.
        """,
        price=4200000,
        features={
            "جنس": "Polyester",
            "کاربرد": "Outdoor",
            "ضدآب": "مقاوم",
            "بند": "ارگونومیک",
            "ظرفیت": "30 لیتر"
        },
        colors=["مشکی", "سبز"]
    )

    create_product(
        name="کوله کوهنوردی Salomon Trail Backpack",
        category_name="کیف و کوله پشتی",
        brand_name="Salomon",
        description="""
        کوله کوهنوردی Salomon برای طبیعت‌گردی
        و فعالیت‌های حرفه‌ای فضای باز طراحی شده است.
        """,
        price=8500000,
        features={
            "ظرفیت": "30 لیتر",
            "جنس": "Ripstop",
            "سیستم تهویه": "دارد",
            "ضدآب": "مقاوم",
            "کاربرد": "کوهنوردی"
        },
        colors=["مشکی", "آبی"]
    )

    create_product(
        name="کیف دوچرخه Shimano Cycling Bag",
        category_name="کیف و کوله پشتی",
        brand_name="Shimano",
        description="""
        کیف دوچرخه Shimano برای حمل ابزار و لوازم جانبی دوچرخه
        در مسیرهای ورزشی و سفر طراحی شده است.
        """,
        price=3000000,
        features={
            "جنس": "Nylon",
            "کاربرد": "دوچرخه سواری",
            "ضدآب": "دارد",
            "اتصال": "روی دوچرخه",
            "وزن": "سبک"
        },
        colors=["مشکی"]
    )

    print("Bags Backpacks category completed successfully")