from django import template
from django.db.models import Count, Max, Min
from django.utils.safestring import mark_safe

from account.models import ShopUser

register = template.Library()

@register.filter()
def to_int(value):
    return int(value)

@register.filter()
def to_str(value):
    return str(value)


@register.filter()
def make_range(current, count):
    return [i for i in range(int(current) + 1, count)]


@register.filter()
def is_in(user_from, user_to):
    if user_to in user_from.followers.all():
        return 'true'
    else:
        return 'false'


@register.filter()
def user_type(user):
    if isinstance(user, ShopUser):
        return 'shop'
    else:
        return 'seller'