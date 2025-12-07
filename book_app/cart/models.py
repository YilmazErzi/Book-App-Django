# cart/models.py (Güncellenmiş)
from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal 

# ------------------------------------
# 📚 Product Modeli (CSV'den gelen veri, artık Book değil!)
# ------------------------------------

class Product(models.Model): # Adını Product yaptık
    external_url = models.URLField(max_length=500, unique=True) 
    name = models.CharField(max_length=255)       
    author = models.CharField(max_length=150)     
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True) 
    
    def __str__(self):
        return self.name

# ------------------------------------
# 🛒 Sepet Modelleri (Product'a bağlanıyor)
# ------------------------------------

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True) 
    
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    # ForeignKey'i artık Product modeline bağlıyoruz!
    product = models.ForeignKey(Product, on_delete=models.CASCADE) 
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product') 

# ------------------------------------
# 💳 Sipariş Modelleri (Product'a bağlanıyor)
# ------------------------------------

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2) 
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='Beklemede') 

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    # ForeignKey'i artık Product modeline bağlıyoruz!
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2) 
    quantity = models.PositiveIntegerField(default=1)
    
    @property
    def get_total_item_price(self):
        return self.price * self.quantity