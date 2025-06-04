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
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt

from account.models import ShopUser, UserAddress, City, ShopSeller
from order.models import Order, OrderItem
from shop.models import Product, Image, ProductFeature, ProductSizeVariant, ProductVariant, ProductColorVariant
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


@login_required
def profile(request):
    user = request.user
    saved_products = ShopUser.objects.get(id=user.id).saved_products.all()
    if Order.objects.filter(user=user).exists():
        user_orders = Order.objects.filter(user=user)
    else:
        user_orders = None
    context = {
        'user': user,
        'user_orders': user_orders,
        'saved_products': saved_products,
    }
    return render(request, 'profile.html', context)


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
            if ShopUser.objects.filter(phone=phone).exists():
                verification_code = ''.join(random.choices('0987654321', k=6))
                request.session['code_create_time'] = datetime.datetime.now().isoformat()
                request.session['verification_code'] = verification_code
                request.session['phone'] = phone
                request.session['login'] = 'login'
                # send_sms_normal(phone, f"{verification_code}\nکد ورود به سبزشاپ:")
                print(verification_code)
                return redirect('account:verification_code')
            else:
                messages.error(request, 'کاربری با همچین شماره تلفنی یافت نشد.')

    else:
        form = PhoneVerificationForm()
    return render(request, 'registration/verification_login.html', {'form': form})


def verification_code(request):
    if request.user.is_authenticated:
        return HttpResponseNotFound('صفحه مورد نظر یافت نشد')
    if request.method == 'POST':
        form = CodeVerificationForm(request.POST)
        if form.is_valid():
            if 'verification_code' in request.session and 'phone' in request.session:
                phone = request.session['phone']
                code = request.session['verification_code']
            else:
                phone = 'invalid'
                code = 'invalid'
            form_code = form.cleaned_data['code']
            if code == form_code:
                code_time = datetime.datetime.fromisoformat(request.session['code_create_time'])
                if datetime.datetime.now() - code_time > datetime.timedelta(minutes=2):
                    messages.error(request, 'کد منقضی شده است')
                    del request.session['phone']
                    del request.session['verification_code']
                    del request.session['code_create_time']
                else:
                    user = ShopUser.objects.get(phone=phone)
                    user.backend = 'account.backends.ShopUserBackend'
                    login(request, user)
                    del request.session['phone']
                    del request.session['verification_code']
                    del request.session['code_create_time']
                    messages.success(request, 'با موفقیت وارد شدید')
                    if 'shopping' in request.session:
                        del request.session['shopping']
                        return redirect('order:create_order')
                    else:
                        return redirect('account:profile')
            else:
                messages.error(request, 'کد تایید نادرست است')
    else:
        form = CodeVerificationForm()
        if 'login' in request.session:
            context = {'form': form, 'login': True}
        else:
            context = {'form': form, 'login': False}
        del request.session['login']
    return render(request, 'registration/verification_code.html', context)


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
            return redirect('account:register_verification_code')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form, 'shopping': False})


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
    order = Order.objects.get(id=order_id)
    if request.user == order.user:
        return render(request, 'order_detail.html', {'order': order})
    else:
        return HttpResponseNotFound('صفحه مورد نظر یافت نشد')


@login_required
def create_address(request):
    if request.method == 'POST':
        province_id = request.POST.get('province')
        form = CreateAddressForm(request.POST, province_id=province_id)
        if form.is_valid():
            cd = form.cleaned_data
            UserAddress.objects.create(
                user=request.user,
                province=cd['province'],
                city=cd['city'],
                address=cd['address'],
                house_number=cd['house_number'],
                postal_code=cd['postal_code']
            )
            messages.success(request, 'آدرس اضافه شد')
            return redirect('order:create_order')

    else:
        form = CreateAddressForm()
        template = render_to_string('create_address.html', {'form': form}, request=request)
        return JsonResponse({'template': template})


@login_required
def create_address_from_profile(request):
    if request.method == 'POST':
        province_id = request.POST.get('province')
        form = CreateAddressForm(request.POST, province_id=province_id)
        if form.is_valid():
            cd = form.cleaned_data
            UserAddress.objects.create(
                user=request.user,
                province=cd['province'],
                city=cd['city'],
                address=cd['address'],
                house_number=cd['house_number'],
                postal_code=cd['postal_code']
            )
            messages.success(request, 'آدرس اضافه شد')
            return redirect('account:addresses')
    else:
        form = CreateAddressForm()
        template = render_to_string('create_address.html', {'form': form}, request=request)
        return JsonResponse({'template': template})


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
        form = EditShopUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'اطلاعات با موفقیت ویرایش شد')
    else:
        form = EditShopUserForm(instance=user)
    context = {
        'form': form,
        'user': user,
    }
    return render(request, 'edit_shopuser.html', context)


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
    user = request.user
    user_addresses = UserAddress.objects.filter(user=user)
    return render(request, 'addresses.html', context={'addresses': user_addresses})


@login_required
def remove_address(request):
    item_id = request.POST.get('item_id')
    print(item_id)
    try:
        address = UserAddress.objects.get(id=item_id)
        address.delete()
        return JsonResponse(data={'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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
