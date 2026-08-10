import datetime
from django.forms import modelformset_factory
import http

import requests
from django.contrib.auth import logout, login, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import render, redirect, get_object_or_404
import random
from django.contrib import messages
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt

from account.models import ShopUser, UserAddress, City, ShopSeller, Province
from cart.cart import Cart
from order.models import Order, OrderItem, ReturnProduct, ReturnOrder
from shop.models import Product, Image, ProductFeature, ProductSizeVariant, ProductVariant, ProductColorVariant, \
    ProductComment, CommentPoint
from sms.send_sms import send_sms_normal
from account.forms import PhoneVerificationForm, CodeVerificationForm, UsernamePasswordLoginForm, RegisterForm, \
    CreateAddressForm, EditShopUserForm, ChangePhoneForm, NewProduct, UploadImageForm, \
    ProductFeatureForm, ProductImageForm
from django.http import HttpResponseNotFound, JsonResponse


def clear_verification_code(request):
    if request.method == 'POST':
        # Remove the verification code from the session
        if 'verification_code' in request.session:
            del request.session['verification_code']
        return JsonResponse({'status': 'success'}, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum

@login_required
def profile(request):

    user = request.user


    saved_products = user.saved_products.all()


    user_orders = Order.objects.filter(
        user=user
    ).prefetch_related(
        'items__product'
    )


    addresses = user.addresses.all()



    return_products = ReturnProduct.objects.filter(
        return_order__order__user=user
    ).select_related(
        'product',
        'return_order',
        'return_order__order'
    )



    cart = Cart(request)



    total_orders_cost = user_orders.aggregate(
        total=Sum('final_cost')
    )['total'] or 0

    default_address = (
            addresses.filter(is_default=True).first()
            or
            addresses.first()
    )

    # ==============================
    # User Comments
    # ==============================

    user_comments = ProductComment.objects.filter(
        user=request.user,
        is_active=True
    ).select_related(
        'product'
    ).prefetch_related(
        'comment_points__point'
    )



    # ==============================
    # Comment Points
    # ==============================

    comment_points_list = CommentPoint.objects.all()



    context = {

        'user': user,


        # summary

        'user_orders': user_orders,

        'saved_products': saved_products,

        'addresses': addresses,

        'return_products': return_products,


        'total_orders_cost': total_orders_cost,

        'cart_count': len(cart),

        'wishlist_count': saved_products.count(),

        'orders_count': user_orders.count(),

        'default_address': default_address,



        # products summary

        'summary_products': saved_products[:3],



        # comments

        'user_comments': user_comments,

        'comment_points_list': comment_points_list,

    }



    return render(
        request,
        'profile.html',
        context
    )


def logout_view(request):
    logout(request)
    messages.success(request, 'با موفقیت خارج شدید')
    return redirect(request.META.get('HTTP_REFERER'))


def login_choice(request):
    if request.user.is_authenticated:
        return HttpResponseNotFound('صفحه مورد نظر یافت نشد')
    if request.path == '/order/login/':
        request.session['shopping'] = True
    return render(request, 'registration/login_choice.html')


def verification_login(request):
    if request.user.is_authenticated:
        return HttpResponseNotFound('صفحه مورد نظر یافت نشد')

    if request.method == 'POST':
        form = PhoneVerificationForm(request.POST)

        if form.is_valid():
            phone = form.cleaned_data['phone']

            verification_code = ''.join(
                random.choices('0123456789', k=6)
            )

            # ذخیره اطلاعات تأیید در session
            request.session['code_create_time'] = datetime.datetime.now().isoformat()
            request.session['verification_code'] = verification_code
            request.session['phone'] = phone

            # فعلاً ارسال پیامک نداریم
            print(f'VERIFICATION CODE for {phone}: {verification_code}')

            return redirect('account:verification_code')

    else:
        form = PhoneVerificationForm()

    return render(
        request,
        'registration/verification_login.html',
        {'form': form}
    )

def merge_guest_wishlist(request, user):

    wishlist = request.session.get('wishlist', [])

    if not wishlist:
        return

    # فقط محصولاتی که واقعاً وجود دارند
    product_ids = Product.objects.filter(
        id__in=wishlist
    ).values_list('id', flat=True)

    # انتقال به علاقه‌مندی‌های کاربر
    user.saved_products.add(*product_ids)

    # پاک کردن wishlist مهمان
    request.session['wishlist'] = []
    request.session.modified = True


def verification_code(request):
    if request.user.is_authenticated:
        return HttpResponseNotFound('صفحه مورد نظر یافت نشد')

    phone = request.session.get('phone')

    # بررسی وجود داشتن اکانت با این شماره
    account_exists = False

    if phone:
        account_exists = ShopUser.objects.filter(
            phone=phone
        ).exists()

    if request.method == 'POST':

        form = CodeVerificationForm(request.POST)

        if form.is_valid():

            form_code = form.cleaned_data['code']

            phone = request.session.get('phone')
            code = request.session.get('verification_code')
            code_create_time = request.session.get('code_create_time')

            # اطلاعات تأیید وجود ندارد
            if not phone or not code or not code_create_time:

                messages.error(
                    request,
                    'کد تأیید نامعتبر است.'
                )

                return redirect(
                    'account:verification_login'
                )

            # دوباره بررسی وجود اکانت
            account_exists = ShopUser.objects.filter(
                phone=phone
            ).exists()

            # بررسی کد
            if code != form_code:

                messages.error(
                    request,
                    'کد تایید نادرست است'
                )

                return render(
                    request,
                    'registration/verification_code.html',
                    {
                        'form': form,
                        'account_exists': account_exists,
                        'phone': phone,
                    }
                )

            # بررسی زمان انقضا
            code_time = datetime.datetime.fromisoformat(
                code_create_time
            )

            if (
                datetime.datetime.now() - code_time
                > datetime.timedelta(minutes=2)
            ):

                messages.error(
                    request,
                    'کد منقضی شده است'
                )

                request.session.pop('phone', None)
                request.session.pop(
                    'verification_code',
                    None
                )
                request.session.pop(
                    'code_create_time',
                    None
                )

                return redirect(
                    'account:verification_login'
                )

            # ==========================================
            # کد صحیح است
            # ==========================================

            user = ShopUser.objects.filter(phone=phone).first()

            if user:

                user.backend = 'account.backends.ShopUserBackend'

                login(request, user)

                # انتقال علاقه‌مندی‌های مهمان به حساب کاربر
                merge_guest_wishlist(request, user)

                # پاک کردن اطلاعات موقت
                request.session.pop('phone', None)
                request.session.pop('verification_code', None)
                request.session.pop('code_create_time', None)

                if 'shopping' in request.session:
                    request.session.pop('shopping', None)
                    return redirect('order:create_order')


                messages.success(
                    request,
                    'با موفقیت وارد شدید'
                )

                if 'shopping' in request.session:

                    request.session.pop(
                        'shopping',
                        None
                    )

                    return redirect(
                        'order:create_order'
                    )

                return redirect(
                    'account:profile'
                )

            # ==========================================
            # کاربر جدید است
            # ==========================================

            request.session['verified_phone'] = phone

            request.session.pop(
                'phone',
                None
            )
            request.session.pop(
                'verification_code',
                None
            )
            request.session.pop(
                'code_create_time',
                None
            )

            return redirect(
                'account:register'
            )

    else:

        form = CodeVerificationForm()

    return render(
        request,
        'registration/verification_code.html',
        {
            'form': form,
            'account_exists': account_exists,
            'phone': phone,
        }
    )


def regenerate_verification_code(request):
    verification_code = ''.join(random.choices('0987654321', k=6))
    del request.session['code_create_time']
    del request.session['verification_code']
    request.session['code_create_time'] = datetime.datetime.now().isoformat()
    request.session['verification_code'] = verification_code
    print(verification_code)
    form = CodeVerificationForm()
    return render(request, 'registration/verification_code.html', {'form': form})


def username_password_login(request):
    if request.user.is_authenticated:
        return HttpResponseNotFound('صفحه مورد نظر یافت نشد')
    if request.method == 'POST':
        form = UsernamePasswordLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['phone']
            password = form.cleaned_data['password']
            if ShopUser.objects.filter(phone=username).exists():
                user = ShopUser.objects.get(phone=username)
                user = authenticate(request, username=username, password=password)
                if isinstance(user, ShopUser) and user is not None:
                    user.backend = 'account.backends.ShopUserBackend'
                if user.check_password(password):
                    login(request, user)
                    messages.success(request, 'با موفقیت وارد شدید')
                    if 'shopping' in request.session:
                        del request.session['shopping']
                        return redirect('order:create_order')
                    else:
                        return redirect('account:profile')
                else:
                    messages.error(request, 'گذرواژه نادرست است')
            else:
                messages.error(request, 'کاربری با همچین شماره تلفنی وجود ندارد.')
    else:
        form = UsernamePasswordLoginForm()
    return render(request, 'registration/password_login.html', {'form': form})


def register(request):

    if request.user.is_authenticated:
        return HttpResponseNotFound('صفحه مورد نظر یافت نشد')

    phone = request.session.get('verified_phone')

    if not phone:
        messages.error(
            request,
            'ابتدا شماره تلفن خود را تأیید کنید.'
        )
        return redirect('account:verification_login')

    if request.method == 'POST':

        form = RegisterForm(request.POST)

        if form.is_valid():

            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data.get('email')

            # بررسی مجدد شماره
            if ShopUser.objects.filter(phone=phone).exists():

                messages.error(
                    request,
                    'این شماره تلفن قبلاً ثبت شده است.'
                )

                request.session.pop(
                    'verified_phone',
                    None
                )

                return redirect(
                    'account:verification_login'
                )

            # ساخت کاربر
            user = ShopUser.objects.create(
                phone=phone,
                first_name=first_name,
                last_name=last_name
            )

            # انتقال علاقه‌مندی‌های مهمان
            merge_guest_wishlist(request, user)

            # عدم استفاده از پسورد
            user.set_unusable_password()
            user.save()

            # ورود خودکار
            user.backend = 'account.backends.ShopUserBackend'
            login(request, user)

            # پاک کردن شماره تأییدشده
            request.session.pop(
                'verified_phone',
                None
            )

            messages.success(
                request,
                'اکانت شما با موفقیت ساخته شد | خوش آمدید'
            )

            if 'shopping' in request.session:

                request.session.pop(
                    'shopping',
                    None
                )

                return redirect(
                    'order:create_order'
                )

            return redirect(
                'account:profile'
            )

    else:

        form = RegisterForm()

    return render(
        request,
        'registration/register.html',
        {
            'form': form,
            'shopping': 'shopping' in request.session,
        }
    )


def register_verification_code(request):
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
                    print('im there')
                    user = ShopUser.objects.create(phone=phone, first_name=first_name, last_name=last_name)
                    print('create')
                    user.backend = 'account.backends.ShopUserBackend'
                    user.set_password(password)
                    print('set pass')
                    user.save()
                    print('save')
                    login(request, user)
                    print('login')
                    messages.success(request, 'اکانت شما با موفقیت ساخته شد | خوش آمدید')
                    del request.session['phone']
                    del request.session['first_name']
                    del request.session['last_name']
                    del request.session['password']
                    del request.session['verification_code']
                    return redirect('account:profile')
            else:
                messages.error(request, 'کد تایید نادرست است')
    else:
        form = CodeVerificationForm()
    return render(request, 'registration/verification_code.html', {'form': form})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product'),
        pk=order_id,
        user=request.user
    )

    return_orders = ReturnOrder.objects.filter(
        order=order
    ).prefetch_related(
        'return_products__product'
    )

    return render(request, 'order_detail.html', {
        'order': order,
        'return_orders': return_orders,
    })


@login_required
def create_address(request):

    if request.method == 'POST':

        province_id = request.POST.get('province')

        form = CreateAddressForm(
            request.POST,
            province_id=province_id
        )


        if form.is_valid():

            cd = form.cleaned_data


            city_value = cd['city']


            if str(city_value).isdigit():

                city_name = City.objects.get(
                    id=int(city_value)
                ).name

            else:

                city_name = str(city_value)



            UserAddress.objects.create(

                user=request.user,

                province=cd['province'].name,

                city=city_name,

                address=cd['address'],

                house_number=cd['house_number'],

                postal_code=cd['postal_code'],

                is_default=(
                    not UserAddress.objects.filter(
                        user=request.user
                    ).exists()
                )

            )


            messages.success(
                request,
                'آدرس اضافه شد'
            )


            return redirect(
                'order:create_order'
            )


    else:

        form = CreateAddressForm()



    template = render_to_string(
        'create_address.html',
        {
            'form': form
        },
        request=request
    )


    return JsonResponse({
        'template': template
    })



@login_required
def create_address_from_profile(request):

    if request.method == 'POST':

        province_id = request.POST.get('province')


        form = CreateAddressForm(
            request.POST,
            province_id=province_id
        )


        if form.is_valid():

            cd = form.cleaned_data


            city_value = cd['city']


            if str(city_value).isdigit():

                city_name = City.objects.get(
                    id=int(city_value)
                ).name

            else:

                city_name = str(city_value)



            UserAddress.objects.create(

                user=request.user,

                province=cd['province'].name,

                city=city_name,

                address=cd['address'],

                house_number=cd['house_number'],

                postal_code=cd['postal_code'],

                is_default=(
                    not UserAddress.objects.filter(
                        user=request.user
                    ).exists()
                )

            )

            messages.success(
                request,
                'آدرس اضافه شد'
            )

            return redirect(
                reverse('account:profile') + '?tab=addresses'
            )


    else:

        form = CreateAddressForm()



    template = render_to_string(
        'create_address.html',
        {
            'form': form
        },
        request=request
    )


    return JsonResponse({
        'template': template
    })


@login_required
def edit_address(request, address_id):

    address = get_object_or_404(
        UserAddress,
        id=address_id,
        user=request.user
    )


    if request.method == "POST":

        province_id = request.POST.get("province")

        form = CreateAddressForm(
            request.POST,
            province_id=province_id
        )


        if form.is_valid():

            cd = form.cleaned_data


            address.province = cd['province'].name
            address.city = City.objects.get(
                id=cd['city']
            ).name

            address.address = cd['address']
            address.house_number = cd['house_number']
            address.postal_code = cd['postal_code']

            address.save()


            messages.success(
                request,
                "آدرس با موفقیت ویرایش شد."
            )


            return redirect(
                "account:profile"
            )


    else:

        province = Province.objects.filter(
            name=address.province
        ).first()


        city = City.objects.filter(
            name=address.city,
            province=province
        ).first()


        form = CreateAddressForm(
            province_id=province.id if province else None,
            selected_city_id=city.id if city else None
        )


        form.initial = {

            "province": province.id if province else None,

            "city": city.id if city else None,

            "address": address.address,

            "house_number": address.house_number,

            "postal_code": address.postal_code

        }

        template = render_to_string(
            "edit_address.html",
            {
                "form": form,
                "address": address
            },
            request=request
        )


        return JsonResponse(
            {
                "template": template
            }
        )


@login_required
def load_cities(request):
    province_id = request.GET.get('province_id')
    cities = City.objects.filter(province_id=province_id)
    city_choices = list(cities.values('id', 'name'))
    return JsonResponse(city_choices, safe=False)


def login_seller(request):
    if request.method == 'POST':
        form = UsernamePasswordLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['phone']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if isinstance(user, ShopSeller) and user is not None:
                user.backend = 'account.backends.ShopSellerBackend'
                if user.check_password(password):
                    login(request, user)
                    messages.success(request, 'با موفقیت وارد شدید')
                    return redirect('shop:product_list')
                else:
                    messages.error(request, 'گذرواژه نادرست است')
            else:
                messages.error(request, 'فروشنده ای با همچین شماره تلفنی وجود ندارد.')
    else:
        form = UsernamePasswordLoginForm()
    return render(request, 'registration/password_login.html', {'form': form, 'seller': True})


@login_required
def edit_profile(request):

    user = request.user

    if request.method == 'POST':

        form = EditShopUserForm(
            request.POST,
            instance=user
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'اطلاعات با موفقیت ویرایش شد'
            )

            return redirect(
                reverse('account:profile') + '?tab=account'
            )

    else:

        form = EditShopUserForm(
            instance=user
        )


    return render(
        request,
        'edit_shopuser.html',
        {
            'form': form,
            'user': user,
        }
    )


@login_required
def change_phone(request):
    if request.method == 'POST':
        form = ChangePhoneForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            verification_code = ''.join(random.choices('0987654321', k=6))
            print(verification_code)
            request.session['code_create_time'] = datetime.datetime.now().isoformat()
            request.session['verification_code'] = verification_code
            request.session['phone'] = phone
            code_form = CodeVerificationForm()
            template = render_to_string('change_phone_code.html', context={'form': code_form}, request=request)
            return JsonResponse({'template': template})
        else:
            template = render_to_string('change_phone.html', context={'form': form}, request=request)
            return JsonResponse({'template': template, 'errors': form.errors}, status=400)
    else:
        form = ChangePhoneForm()
        template = render_to_string('change_phone.html', context={'form': form}, request=request)
        return JsonResponse({'template': template})


@login_required
def change_phone_code(request):
    form = CodeVerificationForm(request.POST)
    if form.is_valid():
        user_code = form.cleaned_data['code']
        code = request.session['verification_code']
        if user_code == code:
            user = request.user
            user.phone = request.session['phone']
            user.save()
            del request.session['code_create_time']
            del request.session['verification_code']
            del request.session['phone']
            messages.success(request, 'شماره تلفن با موفقیت تغییر یافت')
            return redirect('account:edit_profile')
        else:
            messages.error(request, 'کد تایید اشتباه است')
            return redirect('account:edit_profile')


class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'password_change_form.html'

    def form_valid(self, form):
        form.save()
        update_session_auth_hash(self.request, form.user)
        messages.success(self.request, 'گذرواژه شما با موفقیت تغییر یافت')
        return redirect('account:edit_profile')


@login_required
def addresses(request):

    user_addresses = UserAddress.objects.filter(
        user=request.user
    ).order_by(
        "-is_default",
        "-id"
    )

    return render(
        request,
        "addresses.html",
        {
            "addresses": user_addresses
        }
    )


@login_required
def remove_address(request):

    item_id = request.POST.get("item_id")


    try:

        address = UserAddress.objects.get(
            id=item_id,
            user=request.user
        )


        # جلوگیری از حذف آدرس پیشفرض
        if address.is_default:

            return JsonResponse(
                {
                    "success": False,
                    "message": "آدرس پیشفرض قابل حذف نیست."
                },
                status=400
            )


        address.delete()


        return JsonResponse(
            {
                "success": True
            }
        )


    except UserAddress.DoesNotExist:

        return JsonResponse(
            {
                "success": False,
                "message": "آدرس پیدا نشد."
            },
            status=404
        )


@login_required
def set_default_address(request, address_id):

    address = get_object_or_404(
        UserAddress,
        id=address_id,
        user=request.user
    )

    UserAddress.objects.filter(
        user=request.user
    ).update(
        is_default=False
    )

    address.is_default = True
    address.save()

    return JsonResponse({
        "success": True
    })


@login_required
def seller_profile(request):
    user = request.user
    recent_products = Product.objects.filter(seller=user)[:4]
    recent_sails = OrderItem.objects.filter(product__seller=user).order_by('-order__created')[:4]
    print(recent_sails)
    context = {
        'recent_products': recent_products,
        'recent_sails': recent_sails,
        'user': user,
    }
    return render(request, 'seller_profile.html', context)


@login_required
def seller_products(request):
    products = Product.objects.filter(seller=request.user)
    return render(request, 'seller_products.html', context={'products': products})


@login_required
def add_product(request):
    if isinstance(request.user, ShopSeller):
        ProductFeatureFormSet = modelformset_factory(ProductFeature, fields=('name', 'value'), extra=1, can_delete=False)
        ProductImageFormSet = modelformset_factory(Image, fields=('image_file',), extra=1, can_delete=False)
        ProductSizeFormset = modelformset_factory(ProductSizeVariant, fields=('size',), extra=2, can_delete=False)
        ProductColorFormset = modelformset_factory(ProductColorVariant, fields=('color',), extra=2, can_delete=False)

        if request.method == 'POST':
            form = NewProduct(request.POST)
            img_form = UploadImageForm(request.POST, request.FILES)
            more_img_form = ProductImageFormSet(request.POST, request.FILES, queryset=Image.objects.none(), prefix='img')
            feature_formset = ProductFeatureFormSet(request.POST, queryset=ProductFeature.objects.none(), prefix='feature')
            size_formset = ProductSizeFormset(request.POST, queryset=ProductSizeVariant.objects.none(), prefix='size')
            color_formset = ProductColorFormset(request.POST, queryset=ProductColorVariant.objects.none(), prefix='color')

            has_size_option = request.POST.get('has_size_option') == 'on'
            has_color_option = request.POST.get('has_color_option') == 'on'

            if (form.is_valid() and img_form.is_valid() and more_img_form.is_valid() and feature_formset.is_valid()
                    and size_formset.is_valid() and color_formset.is_valid() and color_formset.is_valid()):
                product = form.save(commit=False)
                product.seller = request.user
                product.has_size_option = has_size_option
                product.has_color_option = has_color_option
                product.save()

                image = img_form.save(commit=False)
                image.product = product
                image.save()

                for form in more_img_form:
                    if form.cleaned_data:
                        img = form.save(commit=False)
                        img.product = product
                        img.save()

                for form in feature_formset:
                    feature = form.save(commit=False)
                    feature.product = product
                    feature.save()

                size_variants = []
                if has_size_option:
                    for form in size_formset:
                        size = form.save(commit=False)
                        size.product = product
                        size.save()
                        size_variants.append(size)

                color_variants = []
                if has_color_option:
                    for form in color_formset:
                        color = form.save(commit=False)
                        color.product = product
                        color.save()
                        color_variants.append(color)

                if has_size_option and has_color_option:
                    for size in size_variants:
                        for color in color_variants:
                            ProductVariant.objects.create(product=product, size=size, color=color)
                elif has_color_option:
                    for color in color_variants:
                        ProductVariant.objects.create(product=product, color=color)
                elif has_size_option:
                    for size in size_variants:
                        ProductVariant.objects.create(product=product, size=size)
                else:
                    ProductVariant.objects.create(product=product)

                messages.success(request, 'محصول جدید با موفقیت اضافه شد')
                return redirect('account:seller_products')

        else:
            form = NewProduct()
            img_form = UploadImageForm()
            more_img_form = ProductImageFormSet(queryset=Image.objects.none(), prefix='img')
            feature_formset = ProductFeatureFormSet(queryset=ProductFeature.objects.none(), prefix='feature')
            size_formset = ProductSizeFormset(queryset=ProductSizeVariant.objects.none(), prefix='size')
            color_formset = ProductColorFormset(queryset=ProductColorVariant.objects.none(), prefix='color')

        context = {
            'form': form,
            'img_form': img_form,
            'more_img_form': more_img_form,
            'feature_formset': feature_formset,
            'size_formset': size_formset,
            'color_formset': color_formset,
            'editing': False,
        }
        return render(request, 'add_product.html', context)
    else:
        return HttpResponseNotFound('دسترسی ندارید')


@login_required
def edit_product(request, product_id):
    if isinstance(request.user, ShopSeller):
        # Retrieve the product to edit
        try:
            product = Product.objects.get(id=product_id, seller=request.user)
        except Product.DoesNotExist:
            return HttpResponseNotFound('محصول مورد نظر یافت نشد')

        ProductFeatureFormSet = modelformset_factory(ProductFeature, fields=('name', 'value'), extra=0, can_delete=True)
        ProductImageFormSet = modelformset_factory(Image, fields=['image_file',], extra=0, can_delete=True)
        ProductSizeFormset = modelformset_factory(ProductSizeVariant, fields=('size',), extra=0, can_delete=True)
        ProductColorFormset = modelformset_factory(ProductColorVariant, fields=('color',), extra=0, can_delete=True)

        if request.method == 'POST':
            form = NewProduct(request.POST, instance=product)
            img_form = UploadImageForm(request.POST, request.FILES, instance=product.images.first())
            more_img_form = ProductImageFormSet(request.POST, request.FILES,
                                                queryset=Image.objects.filter(product=product), prefix='img', form_kwargs={})
            feature_formset = ProductFeatureFormSet(
                request.POST, queryset=ProductFeature.objects.filter(product=product), prefix='feature')
            size_formset = ProductSizeFormset(request.POST, queryset=ProductSizeVariant.objects.filter(product=product), prefix='size')
            color_formset = ProductColorFormset(request.POST, queryset=ProductColorVariant.objects.filter(product=product), prefix='color')

            print(feature_formset.errors)
            print(size_formset.errors)
            print(color_formset.errors)
            if (form.is_valid() and img_form.is_valid() and more_img_form.is_valid() and feature_formset.is_valid() and
                    size_formset.is_valid() and color_formset.is_valid()):

                # Update product details
                product = form.save()

                # Update main product image
                image = img_form.save(commit=False)
                image.product = product
                image.save()

                # Add new additional images
                for form in more_img_form:
                    if form.instance.pk:  # Check if it's an existing image
                        if form.cleaned_data.get('DELETE'):
                            form.instance.delete()
                        else:
                            form.save()
                    else:
                        img = form.save(commit=False)
                        img.product = product
                        img.save()

                # Update features
                for feature_form in feature_formset:
                    if feature_form.cleaned_data.get('DELETE'):
                        feature_form.instance.delete()
                    else:
                        feature = feature_form.save(commit=False)
                        feature.product = product
                        feature.save()
                has_size_option = request.POST.get('has_size_option') == 'on'
                has_color_option = request.POST.get('has_color_option') == 'on'
                if product.has_size_option and not has_size_option:
                    product.has_size_option = False
                    product.save()
                    ProductSizeVariant.objects.filter(product=product).delete()
                elif product.has_color_option and not has_color_option:
                    product.has_color_option = False
                    product.save()
                    ProductColorVariant.objects.filter(product=product).delete()

                size_variants = []
                if has_size_option:
                    for form in size_formset:
                        size = form.save(commit=False)
                        size.product = product
                        size.save()
                        size_variants.append(size)

                color_variants = []
                if has_color_option:
                    for form in color_formset:
                        color = form.save(commit=False)
                        color.product = product
                        color.save()
                        color_variants.append(color)

                if has_size_option and has_color_option:
                    for size in size_variants:
                        for color in color_variants:
                            ProductVariant.objects.get_or_create(product=product, size=size, color=color)
                elif has_color_option:
                    for color in color_variants:
                        ProductVariant.objects.get_or_create(product=product, color=color)
                elif has_size_option:
                    for size in size_variants:
                        ProductVariant.objects.get_or_create(product=product, size=size)
                else:
                    ProductVariant.objects.get_or_create(product=product)

                messages.success(request, 'محصول با موفقیت ویرایش شد')
                return redirect('account:seller_products')
        else:
            form = NewProduct(instance=product)
            img_form = UploadImageForm(instance=product.images.first())
            queryset = Image.objects.filter(product=product).order_by('id')
            queryset = queryset.exclude(id=queryset.first().id)
            more_img_form = ProductImageFormSet(queryset=queryset, prefix='img')
            feature_formset = ProductFeatureFormSet(queryset=ProductFeature.objects.filter(product=product),
                                                    prefix='feature')
            size_formset = ProductSizeFormset(queryset=ProductSizeVariant.objects.filter(product=product), prefix='size')
            color_formset = ProductColorFormset(queryset=ProductColorVariant.objects.filter(product=product), prefix='color')

        context = {
            'form': form,
            'img_form': img_form,
            'more_img_form': more_img_form,
            'feature_formset': feature_formset,
            'product': product,
            'size_formset': size_formset,
            'color_formset': color_formset,
            'editing': True,
        }
        return render(request, 'add_product.html', context)
    else:
        return HttpResponseNotFound('دسترسی ندارید')


@login_required
def make_available(request):
    if isinstance(request.user, ShopSeller):
        if request.method == 'POST':
            product_id = request.session['product_id']
            availability_number = request.POST.get('availability_number')
            product = get_object_or_404(Product, id=product_id)
            product.is_available = True
            product.inventory = availability_number
            product.save()
            del request.session['product_id']
            mess = f"کالای مورد نظر به تعداد {availability_number} عدد موجود شد"
            messages.success(request, mess)
            return redirect('account:seller_products')
        else:
            product_id = request.GET.get('product_id')
            request.session['product_id'] = product_id
            template = render_to_string('availability_number.html', request=request)
            return JsonResponse({'template': template})


    else:
        return HttpResponseNotFound('دسترسی ندارید')


@login_required
def make_unavailable(request):
    if isinstance(request.user, ShopSeller):
        if request.method == 'POST':
            product_id = request.session['product_id']
            product = get_object_or_404(Product, id=product_id)
            product.is_available = False
            product.inventory = 0
            product.save()
            del request.session['product_id']
            messages.success(request, 'کالای مورد نظر با موفقیت ناموجود شد')
            return redirect('account:seller_products')
        else:
            product_id = request.GET.get('product_id')
            product = get_object_or_404(Product, id=product_id)
            request.session['product_id'] = product_id
            template = render_to_string('unavailability_confirm.html', request=request,
                                        context={'product': product})
            return JsonResponse({'template': template})


    else:
        return HttpResponseNotFound('دسترسی ندارید')
