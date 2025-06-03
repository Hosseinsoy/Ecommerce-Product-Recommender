from rest_framework.serializers import ModelSerializer

from account.models import ShopUser
from shop.models import Product, ProductFeature


class ProductFeatureSerializer(ModelSerializer):
    class Meta:
        model = ProductFeature
        fields = ['name', 'value']


class ProductSerializer(ModelSerializer):
    features = ProductFeatureSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'off_price', 'description', 'features']


class ShopUserSerializer(ModelSerializer):
    class Meta:
        model = ShopUser
        fields = ['id', 'phone', 'date_joined', 'is_active', 'is_staff']


class ShopUserRegisterSerializer(ModelSerializer):
    class Meta:
        model = ShopUser
        fields = ['phone', 'first_name', 'last_name', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = ShopUser.objects.create(phone=validated_data['phone'], first_name=validated_data['first_name'], last_name=validated_data['last_name'])
        user.set_password(validated_data['password'])
        user.save()
        return user
