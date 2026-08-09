from django.db import models
from django.contrib.auth.models import Permission
from djangospice.database.models import BaseModel, OptionModel 


class Category(OptionModel):
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "categories"
    

class App(BaseModel):
    name = models.CharField(max_length=100, unique=True, editable=False)
    label = models.CharField(max_length=100, editable=False)
    verbose_name = models.CharField(max_length=100)
    url = models.CharField(max_length=200, editable=False, blank=True, null=True)
    icon = models.CharField(max_length=200, editable=False, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    is_service = models.BooleanField(default=False)
    description = models.CharField(max_length=255, blank=True, null=True, editable=False)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, blank=True, null=True)
    permissions = models.ManyToManyField(Permission, related_name="apps", editable=False)

    class Meta:
        ordering = ["name"]
        verbose_name = "App"
        verbose_name_plural = "apps"

    def __str__(self):
        return self.verbose_name

    def activate(self):
        self.is_active = True
        return self
    
    def deactiate(self):
        self.is_active = False
        return self
    
    def set_service(self):
        self.is_service = True
        return self
    
    def unset_service(self):
        self.is_service = False
        return self

    def get_instance(cls, app_name):
        return cls.objects.filter(name=app_name).first()
    
   