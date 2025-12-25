# cart/models.py
from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
# "Bunu alan bunu da aldı" mantığı için sayım yapacak fonksiyonu ekledik:
from django.db.models import Count 

# ------------------------------------
# 📚 Product Modeli
# ------------------------------------

class Product(models.Model):
    external_url = models.URLField(max_length=500, unique=True)
    name = models.CharField(max_length=255)
    author = models.CharField(max_length=150)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return self.name

    def get_recommendations(self, limit=5):
        """
        Bu ürünü içeren siparişleri bulur, o siparişlerdeki 
        diğer ürünleri sayar ve en çok alınanları getirir.
        """
        # Circular Import (Döngüsel İçe Aktarma) hatasını önlemek için 
        # OrderItem modelini fonksiyonun içinde çağırıyoruz.
        from .models import OrderItem 

        # 1. Bu ürünün (self) içinde bulunduğu tüm siparişlerin ID'lerini al
        # (Default related_name 'orderitem_set' kullanılır)
        product_order_ids = self.orderitem_set.values_list('order_id', flat=True)

        # 2. Bu sipariş ID'lerine sahip olan ama bu ürünün KENDİSİ OLMAYAN
        # diğer satırları bul.
        similar_items = OrderItem.objects.filter(order_id__in=product_order_ids)\
                                         .exclude(product=self)\
                                         .values('product')\
                                         .annotate(count=Count('product'))\
                                         .order_by('-count')[:limit]

        # 3. En çok tekrar eden ürünlerin ID'lerini listeye çevir
        recommended_ids = [item['product'] for item in similar_items]

        # 4. Bu ID'lere sahip Product objelerini döndür
        return Product.objects.filter(id__in=recommended_ids)

# ------------------------------------
# 🛒 Sepet Modelleri
# ------------------------------------

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product')

# ------------------------------------
# 💳 Sipariş Modelleri
# ------------------------------------

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='Beklemede')

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    
    @property
    def get_total_item_price(self):
        return self.price * self.quantity

    
class UserPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preference')
    # Kullanıcının ilgi duyduğu anahtar kelimeleri birleştirip burada tutacağız
    # Örn: "school adventure love space politics"
    interest_keywords = models.TextField(default="", blank=True)

    def __str__(self):
        return f"{self.user.username} - İlgi Alanları"