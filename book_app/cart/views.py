from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.db import transaction # Atomik işlem için import ettik
from django.contrib import messages # Kullanıcıya mesaj göstermek için
# Kendi modellerimizi ve utils dosyamızı import ediyoruz
from .models import Cart, CartItem, Product, Order, OrderItem
from .utils import get_current_price_simulated

# --- 1. Sepete Ekleme View'ı (CREATE) ---
@login_required
def add_to_cart(request, product_id):
    # Sepete ekleme genellikle POST isteği ile yapılır
    if request.method == 'POST': 
        
        # Product objesini veritabanından bul
        product = get_object_or_404(Product, id=product_id)
        
        # Kullanıcının sepetini al (yoksa oluştur)
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        # Sepet Öğesini al (yoksa oluştur)
        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart, 
            product=product,
            defaults={'quantity': 1}
        )
        
        if not item_created:
            # Eğer ürün sepette zaten varsa, miktarını 1 artır
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f"{product.name} sepetinizde güncellendi.")
        else:
            messages.success(request, f"{product.name} sepete eklendi.")

        # Sepet detayına yönlendir
        return redirect('cart_detail') 
    
    # POST değilse, öneri listesi ana sayfasına yönlendir (Kendi URL adınızla değiştirin)
    return redirect('book_list') 


# --- 2. Sepet Detay View'ı (READ / Sizin kodunuz) ---
@login_required(login_url='/account/login/')
def cart_detail(request):
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = None 
        
    cart_items_data = []
    total_cart_price = Decimal('0.00')

    if cart:
        for item in cart.items.all():
            
            # Dinamik Fiyatı Çekme
            current_price = get_current_price_simulated(item.product.id)
            
            # Ürün Toplam Maliyetini Hesaplama
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


# --- 3. Sepetten Silme View'ı (DELETE) ---
@login_required
def remove_from_cart(request, item_id):
    if request.method == 'POST':
        # CartItem'ı bul ve sil
        item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        
        # Kitabın adını mesajda kullanmak için alalım
        product_name = item.product.name
        
        item.delete()
        messages.warning(request, f"'{product_name}' sepetten kaldırıldı.")
        
    return redirect('cart_detail')


# --- 4. Satın Alma ve Sipariş Oluşturma View'ı (Simülasyon) ---
@login_required
@transaction.atomic # Bu, işlemlerin ya tamamen başarılı olmasını ya da tamamen geri alınmasını sağlar
def checkout_and_place_order(request):
    if request.method == 'POST':
        
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items = cart.items.all()
            
            if not cart_items:
                messages.error(request, "Sepetiniz boş olduğu için sipariş oluşturulamadı.")
                return redirect('cart_detail') 

            total_price = Decimal('0.00')
            order_items_to_create = []

            # 1. Sepeti ve Anlık Fiyatları Dolaşarak Toplamı Hesapla
            for item in cart_items:
                # Satın alma anındaki ANLIK fiyatı çek ve dondur
                current_price = get_current_price_simulated(item.product.id)
                item_total = item.quantity * current_price
                total_price += item_total
                
                # OrderItem için verileri hazırla
                order_items_to_create.append({
                    'product': item.product,
                    'price': current_price,
                    'quantity': item.quantity
                })

            # 2. Yeni Sipariş (Order) oluştur
            order = Order.objects.create(
                user=request.user,
                total_price=total_price,
                status='Tamamlandı (Simülasyon)'
            )

            # 3. OrderItem'ları toplu olarak oluştur
            order_item_objects = [
                OrderItem(order=order, product=data['product'], price=data['price'], quantity=data['quantity'])
                for data in order_items_to_create
            ]
            OrderItem.objects.bulk_create(order_item_objects)

            # 4. Sepeti Temizle
            cart_items.delete() 
            
            messages.success(request, f"Tebrikler! Siparişiniz ({order.id} numaralı) başarıyla oluşturuldu.")
            return redirect('order_success', order_id=order.id) 

        except Cart.DoesNotExist:
            messages.error(request, "Sepet bulunamadı.")
            return redirect('cart_detail')
        
    return redirect('cart_detail')

# cart/views.py (En alta ekleyin)

@login_required
def order_success(request, order_id):
    # Sipariş objesini bulur
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order,
        # Siparişin içerisindeki ürünleri de şablona gönderebilirsiniz
        'order_items': order.items.all() 
    }
    # Şablonu bir sonraki adımda oluşturacağız
    return render(request, 'cart/order_success.html', context)