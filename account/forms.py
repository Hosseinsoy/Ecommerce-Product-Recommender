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
    phone = forms.CharField(max_length=11, label='شماره تلفن')

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
    code = forms.CharField(max_length=6, label='کد تایید')

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


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput, label='گذرواژه')
    password2 = forms.CharField(widget=forms.PasswordInput, label='تکرار گذرواؤه')

    class Meta:
        model = ShopUser
        fields = ['phone', 'first_name', 'last_name', 'password1', 'password2']

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('عدم تطابق گذرواژه با تکرار آن')
        return password2

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if ShopUser.objects.filter(phone=phone).exists() or ShopSeller.objects.filter(phone=phone).exists():
            raise forms.ValidationError('این شماره تلفن از قبل وجود دارد')
        elif not phone.isdigit():
            raise forms.ValidationError('شماره تلفن باید عدد باشد.')
        elif len(phone) != 11:
            raise forms.ValidationError('شماره تلفن باید 11 رقم باشد.')
        elif not phone.startswith('09'):
            raise forms.ValidationError('شماره تلفن باید با 09 شروع شود.')
        return phone


class CreateAddressForm(forms.Form):
    province = forms.ModelChoiceField(queryset=Province.objects.all(), label='استان')
    city = forms.ChoiceField(choices=[], label='شهر')
    address = forms.CharField(max_length=100, widget=forms.Textarea, label='ادامه آدرس')
    house_number = forms.CharField(label='پلاک')
    postal_code = forms.CharField(max_length=10, label='کد پستی')

    def __init__(self, *args, **kwargs):
        province_id = kwargs.pop('province_id', None)
        super().__init__(*args, **kwargs)
        if province_id:
            self.fields['city'].choices = [(city.id, city.name) for city in City.objects.filter(province_id=province_id)]
        else:
            self.fields['city'].choices = [('', 'اول استان را انتخاب کنید')]


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
