import csv

from django.contrib import admin

from account.models import UserAddress
from order.models import Order, OrderItem, ReturnProduct, ReturnOrder
import openpyxl
from django.http import HttpResponse

# Register your models here.


def export_to_excel(modeladmin, request, queryset):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="orders_exel.xlsx"'
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'سفارشات'
    ws.append([
        'کد سفارش', 'نام و نام خانوادگی خریدار', 'آدرس', 'شماره تلفن ', 'تاریخ ایجاد', 'پرداخت'
    ])
    for order in queryset:
        created = order.created.replace(tzinfo=None) if order.created else ''
        paid = 'موفق' if order.paid else 'ناموفق'
        ws.append([
            order.id, order.name, order.address, order.phone, created, paid
        ])
    wb.save(response)
    return response


export_to_excel.short_description = 'خروجی اکسل'


def export_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv', headers={'Content-Disposition': 'attachment; filename="orders_csv.csv"'})
    writer = csv.writer(response)
    writer.writerow([
        'کد سفارش', 'نام و نام خانوادگی خریدار', 'آدرس', 'شماره تلفن ', 'تاریخ ایجاد', 'پرداخت'
    ])
    for order in queryset:
        created = order.created.replace(tzinfo=None) if order.created else ''
        paid = 'موفق' if order.paid else 'ناموفق'
        writer.writerow([
            order.id, order.name, order.address, order.phone, created, paid
        ])
    return response

export_to_csv.short_description = 'csv خروجی'

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    raw_id_fields = ('product', )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'address', 'phone', 'paid', 'status', 'created', 'updated')
    list_filter = ('paid', 'created', 'updated')
    inlines = [OrderItemInline]
    actions = [export_to_excel, export_to_csv]
    list_editable = ['status']


class ReturnProductInline(admin.StackedInline):
    model = ReturnProduct
    extra = 0


@admin.register(ReturnOrder)
class ReturnOrderAdmin(admin.ModelAdmin):
    list_display = ('order',)
    inlines = [ReturnProductInline]
