from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from pyhanko_certvalidator import ValidationError

from account.models import ShopUser, UserAddress, Province, City, ShopSeller
from shop.models import Product, Image, ProductFeature


class ShpUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = ShopUser
        fields = ['phone', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if ShopUser.objects.filter(phone=phone).exists() or ShopSeller.objects.filter(phone=phone).exists():
            raise forms.ValidationError('Phone already exist')

        elif not phone.isdigit():
            raise forms.ValidationError('Phone must be numbers')

        elif len(phone) != 11:
            raise forms.ValidationError('Phone must be 11 digits')

        elif not phone.startswith('09'):
            raise ValueError('Phone must start with 09')
        return phone


class ShpSellerCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = ShopSeller
        fields = ['phone', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if ShopUser.objects.filter(phone=phone).exists() or ShopSeller.objects.filter(phone=phone).exists():
            raise forms.ValidationError('Phone already exist')

        elif not phone.isdigit():
            raise forms.ValidationError('Phone must be numbers')

        elif len(phone) != 11:
            raise forms.ValidationError('Phone must be 11 digits')

        elif not phone.startswith('09'):
            raise ValueError('Phone must start with 09')
        return phone

class ShpUserChangedForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = ShopUser
        fields = ['phone', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if ShopUser.objects.filter(phone=phone).exists() or ShopSeller.objects.filter(phone=phone).exists():
            raise forms.ValidationError('Phone already exist')
        elif not phone.isdigit():
            raise forms.ValidationError('Phone must be numbers')

        elif len(phone) != 11:
            raise forms.ValidationError('Phone must be 11 digits')

        elif not phone.startswith('09'):
            raise ValueError('Phone must start with 09')
        return phone


class ShopSellerChangedForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = ShopSeller
        fields = ['phone', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if ShopUser.objects.filter(phone=phone).exists() or ShopSeller.objects.filter(phone=phone).exists():
            raise forms.ValidationError('Phone already exist')
        elif not phone.isdigit():
            raise forms.ValidationError('Phone must be numbers')

        elif len(phone) != 11:
            raise forms.ValidationError('Phone must be 11 digits')

        elif not phone.startswith('09'):
            raise ValueError('Phone must start with 09')
        return phone


class PhoneVerificationForm(forms.Form):
    phone = forms.CharField(max_length=11, label='شماره تلفن', widget=forms.TextInput(attrs={
            'class': 'login-phone-input',
            'placeholder': 'شماره موبایل',
            'autocomplete': 'tel',
        }))

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone.isdigit():
            raise forms.ValidationError('شماره تلفن باید عدد باشد.')
        elif len(phone) != 11:
            raise forms.ValidationError('شماره تلفن باید 11 رقم باشد.')
        elif not phone.startswith('09'):
            raise forms.ValidationError('شماره تلفن باید با 09 شروع شود.')
        return phone


class ChangePhoneForm(forms.Form):
    phone = forms.CharField(max_length=11, label='شماره تلفن جدید')

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if ShopUser.objects.filter(phone=phone).exists():
            raise forms.ValidationError('شماره تلفن وجود دارد')
        if not phone.isdigit():
            raise forms.ValidationError('شماره تلفن باید عدد باشد.')
        elif len(phone) != 11:
            raise forms.ValidationError('شماره تلفن باید 11 رقم باشد.')
        elif not phone.startswith('09'):
            raise forms.ValidationError('شماره تلفن باید با 09 شروع شود.')
        return phone


class CodeVerificationForm(forms.Form):
    code = forms.CharField(max_length=6, label='کد تایید', widget=forms.TextInput(attrs={
            'class': 'login-phone-input',
            'placeholder': 'کد تائید',
            'autocomplete': 'tel',
        }))

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if not code.isdigit():
            raise forms.ValidationError('کد تائید باید عدد باشد.')
        elif len(code) != 6:
            raise forms.ValidationError('کد تایید باید 11 رقم باشد.')
        return code


class UsernamePasswordLoginForm(forms.Form):
    phone = forms.CharField(max_length=11, label='شماره تلفن')
    password = forms.CharField(widget=forms.PasswordInput, label='گذرواژه')

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone.isdigit():
            raise forms.ValidationError('شماره تلفن باید عدد باشد.')
        elif len(phone) != 11:
            raise forms.ValidationError('شماره تلفن باید 11 رقم باشد.')
        elif not phone.startswith('09'):
            raise forms.ValidationError('شماره تلفن باید با 09 شروع شود.')
        return phone


from django import forms

from .models import ShopUser
from shop.models import Category, Brand


class RegisterForm(forms.ModelForm):
    favorite_categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )

    favorite_brands = forms.ModelMultipleChoiceField(
        queryset=Brand.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )

    max_monthly_budget = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(
            attrs={
                "class": "login-phone-input",
                "placeholder": "بودجه ماهانه (تومان)",
                "min": "0",
            }
        )
    )

    age = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=120,
        widget=forms.NumberInput(
            attrs={
                "class": "login-phone-input",
                "placeholder": "سن",
                "min": "1",
                "max": "120",
            }
        )
    )

    class Meta:

        model = ShopUser

        fields = [
            "first_name",
            "last_name",
            "email",
        ]

        widgets = {

            "first_name": forms.TextInput(
                attrs={
                    "class": "login-phone-input",
                    "placeholder": "نام",
                    "autocomplete": "given-name",
                }
            ),

            "last_name": forms.TextInput(
                attrs={
                    "class": "login-phone-input",
                    "placeholder": "نام خانوادگی",
                    "autocomplete": "family-name",
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "class": "login-phone-input",
                    "placeholder": "ایمیل (اختیاری)",
                    "autocomplete": "email",
                }
            ),
        }

    def clean_email(self):

        email = self.cleaned_data.get("email")

        if not email:
            return None

        if ShopUser.objects.filter(
            email=email
        ).exists():

            raise forms.ValidationError(
                "این ایمیل قبلاً استفاده شده است."
            )

        return email


class CreateAddressForm(forms.Form):

    province = forms.ModelChoiceField(
        queryset=Province.objects.all(),
        label='استان',
        empty_label='استان را انتخاب کنید',
        widget=forms.Select(
            attrs={
                'class': 'form-select custom-address-input',
            }
        )
    )

    city = forms.ChoiceField(
        choices=[],
        label='شهر',
        widget=forms.Select(
            attrs={
                'class': 'form-select custom-address-input',
            }
        )
    )

    address = forms.CharField(
        max_length=100,
        label='ادامه آدرس',
        widget=forms.Textarea(
            attrs={
                'class': 'form-control custom-address-input',
                'rows': 4,
                'placeholder': 'ادامه آدرس را وارد کنید',
            }
        )
    )

    house_number = forms.CharField(
        label='پلاک',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control custom-address-input',
                'placeholder': 'مثلاً ۱۲',
            }
        )
    )

    postal_code = forms.CharField(
        max_length=10,
        label='کد پستی',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control custom-address-input',
                'placeholder': 'کد پستی ۱۰ رقمی',
                'inputmode': 'numeric',
            }
        )
    )

    def __init__(self, *args, **kwargs):

        province_id = kwargs.pop('province_id', None)
        selected_city_id = kwargs.pop('selected_city_id', None)

        super().__init__(*args, **kwargs)

        # اگر استان مشخص شده باشد
        if province_id:

            cities = City.objects.filter(
                province_id=province_id
            )

            self.fields['city'].choices = [
                (city.id, city.name)
                for city in City.objects.filter(province_id=province_id)
            ]

            if selected_city_id:
                self.fields['city'].initial = selected_city_id

        else:

            self.fields['city'].choices = [
                ('', 'ابتدا استان را انتخاب کنید')
            ]


class EditShopUserForm(forms.ModelForm):
    class Meta:
        model = ShopUser
        fields = ['phone', 'email', 'first_name', 'last_name']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if ShopUser.objects.exclude(phone=phone).filter(phone=phone).exists() or ShopSeller.objects.exclude(phone=phone).filter(phone=phone).exists():
            raise forms.ValidationError('این شماره تلفن از قبل وجود دارد')
        elif not phone.isdigit():
            raise forms.ValidationError('شماره تلفن باید عدد باشد.')
        elif len(phone) != 11:
            raise forms.ValidationError('شماره تلفن باید 11 رقم باشد.')
        elif not phone.startswith('09'):
            raise forms.ValidationError('شماره تلفن باید با 09 شروع شود.')
        return phone

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs.update({

                'class':
                    'form-control custom-address-input'

            })

        self.fields['phone'].disabled = True


class NewProduct(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'name', 'description', 'inventory', 'weight', 'price', 'off',]


class UploadImageForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ['image_file']
        labels = {
            'image_file': 'تصویر اصلی'
        }

        def __init__(self, *args, **kwargs):
            super(UploadImageForm, self).__init__(*args, **kwargs)
            self.fields['image_file'] = False


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class ProductFeatureForm(forms.ModelForm):
    class Meta:
        model = ProductFeature
        fields = ['name', 'value']


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ['image_file']

    def clean(self):
        cleaned_data = super().clean()
        image = cleaned_data.get('image_file')

        if not image and self.instance.pk:
            cleaned_data['image_file'] = self.instance.image_file

        return cleaned_data
