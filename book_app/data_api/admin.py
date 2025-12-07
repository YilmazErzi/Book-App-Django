from django.contrib import admin
from .models import Book

# Register your models here.
@admin.register(Book)
class bookview(admin.ModelAdmin):
    list_display = ("title","author","publish_date")
    list_display_links = ("title","author","publish_date")
# Register your models here.
