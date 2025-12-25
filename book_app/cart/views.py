import re  # Özel karakter temizliği için eklendi
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.db import transaction 
from django.contrib import messages 

# Kendi modellerimizi ve yardımcı fonksiyonlarımızı import ediyoruz
from .models import Cart, CartItem, Product, Order, OrderItem, UserPreference
from .utils import get_current_price_simulated

# indexs uygulaması altındaki AI fonksiyonunu çağırıyoruz
from indexs.views import get_ai_recommendations

# --- 1. ANA SAYFA / KİTAP LİSTESİ (Kişiselleştirilmiş Önerilerle) ---
def book_list(request):
    # Temel ürün listesi: En az 1 kere satılmış kitaplar
    products = Product.objects.filter(orderitem__isnull=False).distinct()
    
    # Veritabanı boşsa ilk 20 kitabı göster
    if not products.exists():
        products = Product.objects.all()[:20]

    # --- KİŞİSELLEŞTİRİLMİŞ ÖNERİ MANTIĞI ---
    personalized_products = []
    interest_keywords = ""

    if request.user.is_authenticated:
        try:
            # Kullanıcının geçmiş ilgi alanlarını çek
            pref = UserPreference.objects.get(user=request.user)
            interest_keywords = pref.interest_keywords
            
            if interest_keywords:
                # Temizlenmiş kelimelerle AI'dan 4 kitap alıyoruz
                personalized_products = get_ai_recommendations(interest_keywords, top_n=4)
        except UserPreference.DoesNotExist:
            pass

    context = {
        'products': products,
        'personalized_products': personalized_products,
        'user_interests': interest_keywords
    }
    return render(request, 'cart/book_list.html', context)


# --- 2. SEPETE EKLEME VE İLGİ KAYDETME (TEMİZLEME EKLENDİ) ---
@login_required
def add_to_cart(request, product_id):
    if request.method == 'POST': 
        product = get_object_or_404(Product, id=product_id)
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        # --- KİŞİSELLEŞTİRME VERİSİ TEMİZLEME VE KAYDETME ---
        pref, _ = UserPreference.objects.get_or_create(user=request.user)
        
        # 1. Mevcut kelimeleri al
        current_keywords = set(pref.interest_keywords.lower().split())
        
        # 2. Yeni veriyi (Kitap + Yazar) hazırla ve TEMİZLE
        # [^\w\s] ifadesi harf, rakam ve boşluk dışındaki her şeyi (parantez, hashtag vb.) siler
        new_data_raw = f"{product.name} {product.author}".lower()
        new_data_clean = re.sub(r'[^\w\s]', '', new_data_raw)
        current_keywords.update(new_data_clean.split())
        
        # 3. Eğer arama sorgusu varsa onu da temizleyip ekle
        search_term = request.POST.get('search_query') or request.GET.get('desc')
        if search_term:
            search_clean = re.sub(r'[^\w\s]', '', search_term.lower())
            current_keywords.update(search_clean.split())
            
        # 4. Havuzu güncelle ve son 40 kelimeyle sınırla (Modelin sapmaması için)
        # Çok fazla alakasız kelime birikmesi öneri kalitesini düşürür.
        pref.interest_keywords = " ".join(list(current_keywords)[-40:])
        pref.save()

        # --- SEPETE EKLEME İŞLEMİ ---
        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart, 
            product=product,
            defaults={'quantity': 1}
        )
        
        if not item_created:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f"{product.name} miktarı artırıldı.")
        else:
            messages.success(request, f"{product.name} sepete eklendi.")

        return redirect('cart_detail') 
    
    return redirect('product_detail', product_id=product_id)


# --- 3. ÜRÜN DETAY ---
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    recommendations = product.get_recommendations(limit=4)
    
    context = {
        'product': product,
        'recommendations': recommendations
    }
    return render(request, 'cart/product_detail.html', context)


# --- 4. SEPET DETAY ---
@login_required
def cart_detail(request):
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = None 
        
    cart_items_data = []
    total_cart_price = Decimal('0.00')

    if cart:
        for item in cart.items.all():
            current_price = get_current_price_simulated(item.product.id)
            item_total = item.quantity * current_price
            total_cart_price += item_total

            cart_items_data.append({
                'item_id': item.id,
                'product': item.product, 
                'quantity': item.quantity,
                'unit_price': current_price,
                'item_total': item_total,
                'goodreads_url': item.product.external_url, 
            })

    context = {
        'cart_items': cart_items_data,
        'total_cart_price': total_cart_price,
    }
    return render(request, 'cart/cart_detail.html', context)


# --- 5. SATIN ALMA ---
@login_required
@transaction.atomic 
def checkout_and_place_order(request):
    if request.method == 'POST':
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items = cart.items.all()
            
            if not cart_items:
                messages.error(request, "Sepetiniz boş.")
                return redirect('cart_detail') 

            total_price = Decimal('0.00')
            order = Order.objects.create(user=request.user, total_price=0, status='Tamamlandı')

            for item in cart_items:
                current_price = get_current_price_simulated(item.product.id)
                OrderItem.objects.create(
                    order=order, product=item.product, 
                    price=current_price, quantity=item.quantity
                )
                total_price += item.quantity * current_price

            order.total_price = total_price
            order.save()
            cart_items.delete() 
            
            messages.success(request, "Siparişiniz başarıyla alındı!")
            return redirect('order_success', order_id=order.id) 

        except Cart.DoesNotExist:
            return redirect('cart_detail')
    return redirect('cart_detail')


# --- 6. DİĞER FONKSİYONLAR ---
@login_required
def remove_from_cart(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        item.delete()
        messages.warning(request, "Ürün sepetten kaldırıldı.")
    return redirect('cart_detail')

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'cart/order_success.html', {'order': order, 'order_items': order.items.all()})