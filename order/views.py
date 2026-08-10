import json
import random
import datetime
from io import BytesIO

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseNotFound, HttpResponse, JsonResponse, HttpResponseNotAllowed
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from account.forms import RegisterForm, CodeVerificationForm
from account.models import ShopUser, UserAddress, City
from cart.cart import Cart
from order.forms import CreateOrderForm, ReturnOrderForm
from order.models import OrderItem, Order, ReturnOrder, ReturnProduct
import pdfkit

from shop.models import Product, Image, DiscountCode


# Create your views here.
def shopping_register(request):
    if request.user.is_authenticated:
        return HttpResponseNotFound('صفحه مورد نظر یافت نشد')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            verification_code = ''.join(random.choices('0987654321', k=6))
            request.session['code_create_time'] = datetime.datetime.now().isoformat()
            print(verification_code)
            # send_sms_normal(phone, f"{verification_code}\nکد ورود به سبزشاپ:")
            request.session['verification_code'] = verification_code
            request.session['phone'] = phone
            request.session['first_name'] = form.cleaned_data['first_name']
            request.session['last_name'] = form.cleaned_data['last_name']
            request.session['password'] = form.cleaned_data['password1']
            return redirect('order:shopping_register_verification_code')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form, 'shopping': True})


def shopping_register_verification_code(request):
    if request.user.is_authenticated:
        return HttpResponseNotFound('صفحه مورد نظر یافت نشد')
    if request.method == 'POST':
        form = CodeVerificationForm(request.POST)
        if form.is_valid():
            form_code = form.cleaned_data['code']
            phone = request.session['phone']
            first_name = request.session['first_name']
            last_name = request.session['last_name']
            password = request.session['password']
            code = request.session['verification_code']
            if code == form_code:
                code_time = datetime.datetime.fromisoformat(request.session['code_create_time'])
                if datetime.datetime.now() - code_time > datetime.timedelta(minutes=2):
                    messages.error(request, 'کد منقضی شده است')
                    del request.session['phone']
                    del request.session['verification_code']
                    del request.session['code_create_time']
                else:
                    user = ShopUser.objects.create(phone=phone, first_name=first_name, last_name=last_name)
                    user.set_password(password)
                    user.save()
                    login(request, user)
                    messages.success(request, 'اکانت شما با موفقیت ساخته شد | خوش آمدید')
                    del request.session['phone']
                    del request.session['first_name']
                    del request.session['last_name']
                    del request.session['password']
                    del request.session['verification_code']
                    return redirect('order:create_order')
            else:
                messages.error(request, 'کد تایید نادرست است')
    else:
        form = CodeVerificationForm()
    return render(request, 'registration/verification_code.html', {'form': form})


def order(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.error(request, 'سبد خرید شما خالی است')
        return redirect('cart:cart_detail')
    if request.user.is_authenticated:
        return redirect('order:create_order')
    else:
        return redirect('order:shopping_register')


@login_required
def create_order(request):
    discounted_cost = None
    if 'discounted_cost' in request.session:
        discounted_cost = request.session['discounted_cost']
    cart = Cart(request)
    model_addresses = UserAddress.objects.filter(user=request.user)
    addresses = []
    for address in model_addresses:
        city = address.city
        addr = ''
        addr += address.province + ' | '
        addr += city + ' | '
        addr += address.address + ' | '
        addr += address.house_number + ' | '
        addr += 'کد پستی: ' + address.postal_code
        addresses.append(addr)
    if request.method == 'POST':
        form = CreateOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            if discounted_cost:
                order.final_cost = discounted_cost
            else:
                order.final_cost = cart.final_price()
            if 'discounted_cost' in request.session:
                del request.session['discounted_cost']
            if 'discount_code' in request.session:
                dc = DiscountCode.objects.get(pk=request.session['discount_code'])
                order.discount_code = dc
                del request.session['discount_code']
            order.save()
            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'].product, price=item['product'].product.off_price,
                                         weight=item['product'].product.weight, quantity=item['quantity'],
                                         color=item['product'].color, size=item['product'].size)
            cart.clear()
            return redirect('account:profile')
    else:
        form = CreateOrderForm(initial={'name': request.user.get_full_name(), 'phone': request.user.phone})
    return render(request, 'create_order.html', {"form": form, "cart": cart, 'addresses': addresses,
                                                 'discounted_cost': discounted_cost})


def invoice_pdf(request, order_id):
    pdfkit_config = pdfkit.configuration(wkhtmltopdf='C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe')
    order = Order.objects.get(pk=order_id)
    html_string = render_to_string('invoice.html', {'order': order})
    pdf = pdfkit.from_string(html_string, False, configuration=pdfkit_config)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=' + f"invoice_{order.id}.pdf"
    return response


@login_required
def return_order(request, order_id):

    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    # فقط سفارش متعلق به همین کاربر
    order = get_object_or_404(
        Order,
        pk=order_id,
        user=request.user
    )

    order_products = order.items.all()

    # سفارش باید تحویل شده باشد
    if order.status != 'تحویل مرسوله به مشتری':

        messages.error(
            request,
            'این قابلیت پس از تحویل کالا در دسترس است'
        )

        return JsonResponse({
            'redirect': True,
            'redirect_url': reverse(
                'account:order_detail',
                args=[order_id]
            )
        })

    # زمان تحویل باید وجود داشته باشد و حداکثر 3 روز گذشته باشد
    if (
        order.delivery_time is None
        or timezone.now() - order.delivery_time > datetime.timedelta(days=3)
    ):

        messages.error(
            request,
            'امکان مرجوعی این سفارش وجود ندارد. '
            'از زمان تحویل سفارش بیش از 3 روز گذشته است.'
        )

        return JsonResponse({
            'redirect': True,
            'redirect_url': reverse(
                'account:order_detail',
                args=[order_id]
            )
        })

    # فرم انتخاب محصولات مرجوعی
    order_form = ReturnOrderForm(
        custom_queryset=order_products
    )

    template = render_to_string(
        'return_order.html',
        {
            'form': order_form,
            'order': order,
        },
        request=request
    )

    return JsonResponse({
        'template': template
    })


@login_required
def return_product(request, order_id):

    order = get_object_or_404(
        Order,
        pk=order_id,
        user=request.user
    )

    order_products = order.items.all()

    if request.method == 'POST':

        form = ReturnOrderForm(
            request.POST,
            custom_queryset=order_products
        )

        if form.is_valid():

            products = form.cleaned_data['return_products']

            if not products:
                return JsonResponse({
                    'success': False,
                    'errors': {
                        'return_products': [
                            'حداقل یک محصول را انتخاب کنید.'
                        ]
                    }
                }, status=400)

            return_order = ReturnOrder.objects.create(
                order=order
            )

            for index, product in enumerate(products, start=1):

                quantity = request.POST.get(
                    f'quantity_{product.id}'
                )

                explanation = request.POST.get(
                    f'explanation_{product.id}'
                )

                photo = request.FILES.get(
                    f'photo_{product.id}'
                )

                if not quantity:
                    return JsonResponse({
                        'success': False,
                        'error': f'تعداد مرجوعی برای {product.name} وارد نشده است.'
                    }, status=400)

                quantity = int(quantity)

                # بررسی تعداد مرجوعی
                order_item = order.items.filter(
                    product=product
                ).first()

                if not order_item:
                    return JsonResponse({
                        'success': False,
                        'error': 'محصول انتخاب‌شده متعلق به این سفارش نیست.'
                    }, status=400)

                if quantity < 1 or quantity > order_item.quantity:
                    return JsonResponse({
                        'success': False,
                        'error': (
                            f'تعداد مرجوعی برای {product.name} '
                            f'باید بین 1 تا {order_item.quantity} باشد.'
                        )
                    }, status=400)

                if not explanation:
                    return JsonResponse({
                        'success': False,
                        'error': f'دلیل مرجوعی {product.name} وارد نشده است.'
                    }, status=400)

                if not photo:
                    return JsonResponse({
                        'success': False,
                        'error': f'تصویر {product.name} انتخاب نشده است.'
                    }, status=400)

                ReturnProduct.objects.create(
                    return_order=return_order,
                    product=product,
                    quantity=quantity,
                    explanation=explanation,
                    photo=photo
                )

            return_order.cost = return_order.total_cost()
            return_order.save()

            messages.success(
                request,
                'درخواست مرجوعی با موفقیت ارسال شد. '
                'می‌توانید وضعیت درخواست را از قسمت پیگیری درخواست‌های مرجوعی مشاهده کنید.'
            )

            return redirect(
                'account:order_detail',
                order_id=order.id
            )

        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)


    # GET
    selected_products = request.GET.get(
        'selected_products',
        ''
    )

    product_ids = [
        product_id
        for product_id in selected_products.split(',')
        if product_id
    ]

    product_list = []

    for product_id in product_ids:

        try:
            order_item = order.items.get(
                product_id=product_id
            )

            product_list.append({
                'product': order_item.product,
                'quantity': order_item.quantity
            })

        except order.items.model.DoesNotExist:
            continue

    template = render_to_string(
        'return_product.html',
        {
            'order': order,
            'products': product_list
        },
        request=request
    )

    return JsonResponse({
        'template': template
    })


def show_returns(request, order_id):
    order = Order.objects.get(pk=order_id)
    flag = False
    if order_id not in [item.order_id for item in ReturnOrder.objects.all()]:
        messages.error(request, 'درخواست مرجوعی برای این سفارش ایجاد نشده است')
        flag = True
    if flag:
        return JsonResponse({
            'redirect': True,
            'redirect_url': reverse('account:order_detail', args=[order_id])
        })
    else:
        return_orders = ReturnOrder.objects.filter(order=order).all()
        template = render_to_string('show_return_orders.html', {'orders': return_orders}, request=request)
        return JsonResponse({'template': template})


