from django.contrib import admin

from .models import AppDependency, AppInstallation, AppInstance


class AppDependencyInline(admin.TabularInline):
    model = AppDependency
    extra = 0
    autocomplete_fields = ("app",)


@admin.register(AppInstance)
class AppInstanceAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "package", "version", "status", "enabled")
    list_filter = ("status", "enabled")
    search_fields = ("key", "name", "package", "django_app")
    inlines = (AppDependencyInline,)


@admin.register(AppInstallation)
class AppInstallationAdmin(admin.ModelAdmin):
    list_display = ("app", "action", "version", "successful", "started_at", "completed_at")
    list_filter = ("action", "successful")
    search_fields = ("app__key", "app__name", "version")
    autocomplete_fields = ("app",)
    readonly_fields = ("started_at", "completed_at")

