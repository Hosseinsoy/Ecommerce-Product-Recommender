from django.utils import timezone
from django.db.models.signals import pre_save
from django.dispatch import receiver

from order.models import Order
from sms.send_sms import send_sms_normal


@receiver(pre_save, sender=Order)
def order_status_change(sender, instance,  **kwargs):
    if instance.status == 'آماده سازی سفارش':
        # send_sms_normal(instance.phone, f"{instance.name} عزیز "+f"سفارش شما از فروشنده تحویل و در حال آماده سازی می باشد."+f"{instance.id}شماره سفارش: ")
        print(f"{instance.name} عزیز "+f"سفارش شما از فروشنده تحویل و در حال آماده سازی می باشد."+f"{instance.id}شماره سفارش: ")
    elif instance.status == 'تحویل به پست':
        # send_sms_normal(instance.phone, f"{instance.name} عزیز "+f"سفارش شما به پست تحویل داده شد."+f"{instance.id}شماره سفارش: "+f"\n رهگیری مرسوله:")
        print(f"{instance.name} عزیز "+f"سفارش شما به پست تحویل داده شد."+f"{instance.id}شماره سفارش: "+f"\n رهگیری مرسوله:")
    elif instance.status == 'تحویل مرسوله به مشتری':
        instance.delivery_time = timezone.now()
