from django.contrib import admin
from .models import Product, Cart, CartItem, Order, OrderItem, UserPreference

# --- INLINE MODELLER (İç içe görünüm için) ---

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1  # Yeni ekleme için boş satır sayısı

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('price', 'quantity', 'get_total_item_price') # Sipariş kalemleri genellikle değiştirilmez

# --- ANA MODELLER ---

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "author", "average_rating")
    list_display_links = ("name", "author")
    search_fields = ("name", "author") # Ürün aramayı kolaylaştırır

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user",)
    inlines = [CartItemInline] # Sepet içinde ürünleri göster

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "total_price", "status", "created_at")
    list_filter = ("status", "created_at") # Sağ tarafta filtreleme paneli açar
    inlines = [OrderItemInline] # Sipariş içinde ürünleri göster

@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'interest_keywords')