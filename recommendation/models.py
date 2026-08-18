from django.db import models
from django.conf import settings
# Create your models here.

import uuid

from django.db import models
from django.utils import timezone


class Interaction(models.Model):


    EVENT_TYPES = [

        ("view", "مشاهده"),

        ("wishlist", "علاقه‌مندی"),

        ("cart", "افزودن به سبد"),

        ("purchase", "خرید"),

    ]


    SOURCE_TYPES = [

        ("search", "جستجو"),

        ("home", "صفحه اصلی"),

        ("category", "دسته بندی"),

        ("direct", "مستقیم"),

    ]




    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="interactions"
    )


    product = models.ForeignKey(
        "shop.Product",
        on_delete=models.CASCADE,
        related_name="interactions"
    )


    search_query = models.ForeignKey(
        "shop.SearchQuery",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="interactions"
    )


    # شناسه سشن کاربر
    session_id = models.UUIDField(

        default=uuid.uuid4,

        editable=False,

        db_index=True,

        verbose_name="شناسه نشست"

    )



    source = models.CharField(

        max_length=50,

        choices=SOURCE_TYPES,

        default="direct",

        verbose_name="منبع تعامل"

    )


    event = models.CharField(

        max_length=20,

        choices=EVENT_TYPES,

        verbose_name="نوع تعامل"

    )



    # امتیاز اهمیت تعامل
    interaction_score = models.FloatField(

        default=1,

        verbose_name="امتیاز تعامل"

    )



    timestamp = models.DateTimeField(

        default=timezone.now,

        db_index=True,

        verbose_name="زمان تعامل"

    )



    dwell_time = models.PositiveIntegerField(

        default=0,

        null=True,

        blank=True,

        verbose_name="مدت مشاهده (ثانیه)"

    )



    metadata = models.JSONField(

        default=dict,

        blank=True,

        verbose_name="اطلاعات تکمیلی"

    )



    class Meta:

        ordering = [

            "-timestamp"

        ]


        indexes = [

            models.Index(

                fields=[

                    "user",

                    "timestamp"

                ]

            ),


            models.Index(

                fields=[

                    "session_id",

                    "timestamp"

                ]

            ),


            models.Index(

                fields=[

                    "product",

                    "event"

                ]

            ),


            models.Index(

                fields=[

                    "source"

                ]

            ),

        ]



        verbose_name = "تعامل"

        verbose_name_plural = "تعاملات"




    def save(self, *args, **kwargs):


        scores = {

            "view": 1,

            "wishlist": 3,

            "cart": 5,

            "purchase": 10,

        }


        if not self.interaction_score:

            self.interaction_score = scores.get(

                self.event,

                1

            )


        super().save(
            *args,
            **kwargs
        )




    def __str__(self):

        return (

            f"{self.user.phone} | "

            f"{self.product.name} | "

            f"{self.event}"

        )


class UserPreference(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )


    favorite_categories = models.ManyToManyField(
        'shop.Category',
        blank=True
    )


    favorite_brands = models.ManyToManyField(
        'shop.Brand',
        blank=True
    )


    max_monthly_budget = models.PositiveIntegerField(
        default=0
    )


    age = models.PositiveIntegerField(
        null=True,
        blank=True
    )


    created = models.DateTimeField(
        auto_now_add=True
    )


    updated = models.DateTimeField(
        auto_now=True
    )


    def __str__(self):

        return str(self.user)
