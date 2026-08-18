from django.contrib import admin

from recommendation.models import Interaction
from recommendation.models import UserPreference


# Register your models here.
@admin.register(Interaction)
class IterationAdmin(admin.ModelAdmin):

    list_display = (
        'user__id',
        'product',
        'search_query',
        'event',
        'timestamp',
        'dwell_time',
        'metadata'
    )

    list_filter = (
        'user__id',
        'event',
        'source',
        'timestamp',
    )


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):

    list_display = (
        'user__id',
        'max_monthly_budget',
        'age',
        'created',
    )
