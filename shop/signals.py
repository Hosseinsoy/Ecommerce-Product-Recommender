from django.db.models.signals import pre_save, post_save
from .models import Product
from order.models import OrderItem
from django.dispatch import receiver


@receiver(pre_save, sender=Product)
def calculate_off_price(sender, instance, **kwargs):
    instance.off_price = instance.price - (instance.price * (instance.off / 100))
    if instance.inventory == 0:
        instance.is_available = False
    else:
        instance.is_available = True


@receiver(post_save, sender=OrderItem)
def update_inventory(sender, instance, **kwargs):
    instance.product.inventory = instance.product.inventory - instance.quantity
    instance.product.save()
