# cart/utils.py
from decimal import Decimal
import random

def get_current_price_simulated(product_id):
    """
    Temsili olarak dinamik fiyat çekme işlemini simüle eder.
    Aynı ürün ID'si için her zaman aynı fiyatı döndürerek tutarlılık sağlar.
    """
    # Aynı product_id için her zaman aynı rastgele fiyatı almak için seed kullanıyoruz.
    random.seed(product_id) 
    # Fiyatı 50.00 TL ile 200.00 TL arasında rastgele belirle
    # Fiyatın Decimal hassasiyetinde olması için 100'e böldük.
    price = random.randint(5000, 20000) / 100 
    return Decimal(str(price))