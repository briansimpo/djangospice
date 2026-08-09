from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import App, Category


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ["code", "name"]


@admin.register(App)
class AppAdmin(ModelAdmin):
    list_display = ["verbose_name", "label", "name", "category", "is_active", "is_default", "is_service", "url", "icon"]
    list_display_links = ["verbose_name"]
    search_fields = ["verbose_name"]
    filter_horizontal = ["permissions",]

