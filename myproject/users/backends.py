from django.contrib.auth.backends import BaseBackend
from .models import Users,Admins

class CustomUserBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = Users.objects.get(username=username)
            if user.check_password(password):
                return user
        except Users.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return Users.objects.get(pk=user_id)
        except Users.DoesNotExist:
            return None

class CustomAdminBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            admin = Admins.objects.get(admin_username=username)
            if admin.check_password(password):
                return admin
        except Admins.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return Admins.objects.get(pk=user_id)
        except Admins.DoesNotExist:
            return None