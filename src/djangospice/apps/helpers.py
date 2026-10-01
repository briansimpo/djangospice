from django.http import HttpRequest
from .models import Category
from .services import UserApps


def get_category_list(request: HttpRequest):
    queryset = Category.objects.all()
    return queryset


def get_user_apps(request: HttpRequest):
    if request.user and request.user.is_authenticated:
        user = request.user
        user_apps = UserApps(user)
        return user_apps.get_apps()
