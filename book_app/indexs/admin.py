from django.contrib import admin
from .models import person

# Register your models here.
@admin.register(person)
class personview(admin.ModelAdmin):
    list_display = ("first_name","last_name","project_role","department")
    list_display_links = ("first_name","last_name")