from django.urls import path
from . import views

urlpatterns = [
    # Ana Sepet Sayfası (URL: /cart/)
    # Sepetin içeriğini, dinamik fiyatları ve toplamı gösterir.
    path('', views.cart_detail, name='cart_detail'), 
    
    # Sepete Ürün Ekleme (URL: /cart/add/123/)
    # Genellikle bir öneri listesi sayfasındaki POST isteğiyle tetiklenir.
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    
    # Sepetten Ürün Silme (URL: /cart/remove/456/)
    # Bir CartItem öğesini (Product değil) sepetten siler.
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'), 
    
    # Satın Alma İşlemini Başlatma (URL: /cart/checkout/)
    # Sepeti siparişe dönüştürür, fiyatları dondurur ve sepeti temizler.
    path('checkout/', views.checkout_and_place_order, name='checkout'), 
    
    # Sipariş Başarı Sayfası (URL: /cart/order/789/)
    # Satın alma simülasyonu başarılı olduktan sonra kullanıcıyı yönlendirir.
    path('order/<int:order_id>/', views.order_success, name='order_success'), 
]