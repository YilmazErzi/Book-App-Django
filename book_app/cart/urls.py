# cart/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Ana Sayfa: Artık direkt kitap listesini açacak
    path('', views.book_list, name='book_list'), 
    
    # Diğer yollar aynen kalıyor...
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/checkout/', views.checkout_and_place_order, name='checkout'),
    path('cart/order/<int:order_id>/', views.order_success, name='order_success'),
]