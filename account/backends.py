from django.contrib.auth.backends import BaseBackend
from .models import ShopUser, ShopSeller

class ShopUserBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        try:
            user = ShopUser.objects.get(phone=username)
            if user.check_password(password):
                return user
        except ShopUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return ShopUser.objects.get(pk=user_id)
        except ShopUser.DoesNotExist:
            return None


class ShopSellerBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        try:
            user = ShopSeller.objects.get(phone=username)
            if user.check_password(password):
                return user
        except ShopSeller.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return ShopSeller.objects.get(pk=user_id)
        except ShopSeller.DoesNotExist:
            return None
