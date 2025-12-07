from django.contrib import admin
from .models import Product

# Register your models here.
@admin.register(Product)
class productview(admin.ModelAdmin):
    list_display = ("name","author","average_rating")
    list_display_links = ("name","author","average_rating")
# Register your models here.
