from django.http import HttpResponse
from django.shortcuts import render
from .models import person
from data_api.models import Book 
from cart.models import Product 
import requests
import random
from bs4 import BeautifulSoup
from urllib.parse import quote

# --- AI KÜTÜPHANELERİ ---
import os
import pickle
import pandas as pd
from django.conf import settings
from sklearn.metrics.pairwise import linear_kernel

print("⏳ AI Modeli yükleniyor...")
BASE_DIR = settings.BASE_DIR
DATA_PATH = os.path.join(BASE_DIR, 'data')

try:
    books_df = pickle.load(open(os.path.join(DATA_PATH, 'books_processed.pkl'), 'rb'))
    tfidf_model = pickle.load(open(os.path.join(DATA_PATH, 'tfidf_model.pkl'), 'rb'))
    tfidf_matrix = pickle.load(open(os.path.join(DATA_PATH, 'tfidf_matrix.pkl'), 'rb'))
    print("✅ Model hazır!")
except Exception as e:
    print(f"❌ HATA: Model yüklenemedi. {e}")
    books_df = None

# --- YARDIMCI FONKSİYONLAR ---

def get_ai_recommendations(query, top_n=6):
    if books_df is None: return []
    try:
        query_vec = tfidf_model.transform([query])
        cosine_sim = linear_kernel(query_vec, tfidf_matrix)
        sim_scores = sorted(list(enumerate(cosine_sim[0])), key=lambda x: x[1], reverse=True)[0:top_n]
        book_indices = [i[0] for i in sim_scores]
        return books_df.iloc[book_indices].fillna('').to_dict('records')
    except:
        return []

def get_amazon_data(title):
    """
    Amazon.com.tr üzerinden Fiyat ve Resim çeker.
    Amazon bot korumasını aşmak için Header kullanır.
    """
    try:
        # Amazon TR araması
        search_url = f"https://www.amazon.com.tr/s?k={quote(title)}"
        
        # Bu headerlar Amazon'a "Ben gerçek bir insanım" demek için gereklidir
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.google.com/"
        }
        
        response = requests.get(search_url, headers=headers, timeout=4)
        
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Arama sonuçlarını bul (Amazon'un genel yapısı)
        results = soup.find_all("div", {"data-component-type": "s-search-result"})
        
        if not results:
            return None
            
        # İlk sonucu al
        first_result = results[0]
        data = {}

        # 1. FİYATI ÇEK
        # Amazon fiyatları genellikle 'a-price' class'ı içinde 'a-offscreen' span'ında gizlidir
        price_tag = first_result.find("span", class_="a-price")
        if price_tag:
            offscreen_price = price_tag.find("span", class_="a-offscreen")
            if offscreen_price:
                # "120,50 TL" gibi gelen veriyi temizle
                price_text = offscreen_price.get_text(strip=True).replace("TL", "").strip()
                data['price'] = price_text
        
        # 2. RESMİ ÇEK
        img_tag = first_result.find("img", class_="s-image")
        if img_tag:
            data['image'] = img_tag.get('src')
            
        return data

    except Exception as e:
        # Amazon hata verirse veya bulamazsa sessizce geç
        return None

# --- VIEW FONKSİYONLARI ---

def home(request):
    book = None
    recommendations = []
    query = ""
    mode = "random"

    # 1. RASTGELE KİTAP (SOL KISIM)
    if Book.objects.count() > 0:
        try:
            random_id = random.choice(Book.objects.values_list("id", flat=True))
            url = f"http://127.0.0.1:8000/api/{random_id}"
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                book = response.json()
                # Görsel yoksa Amazon'dan çekmeyi dene
                if not book.get('image_url'):
                    amazon_data = get_amazon_data(book.get("title", ""))
                    if amazon_data:
                        # Amazon'dan fiyat ve resim gelirse kullan
                        if amazon_data.get('price'):
                            book["price"] = amazon_data.get('price')
                        if amazon_data.get('image'):
                            book["image_url"] = amazon_data.get('image')
            else: book = None
        except: book = None 

    # 2. YAPAY ZEKA ÖNERİLERİ
    if 'desc' in request.GET:
        query = request.GET.get('desc')
        if query and len(query) > 1:
            recommendations = get_ai_recommendations(query)
            mode = "search"
            
            for rec in recommendations:
                # --- A. VERİ ÇEKME (AMAZON) ---
                # Önce Amazon'a soralım, gerçek veri var mı?
                amazon_data = get_amazon_data(rec['Book'])
                
                # Varsayılan değerler
                rec['Price'] = None
                
                if amazon_data:
                    # Amazon'da bulduysak oradaki fiyatı ve resmi kullan
                    if amazon_data.get('price'):
                        rec['Price'] = amazon_data['price']
                    if amazon_data.get('image'):
                        rec['Image_URL'] = amazon_data['image']
                
                # --- B. EĞER AMAZON'DA BULAMAZSAK (FALLBACK) ---
                
                # Görsel hala yoksa veri setindekini kullan
                if not rec.get('Image_URL'):
                    img_url = rec.get('Image-URL-M') or rec.get('image_url') or rec.get('Image_URL')
                    rec['Image_URL'] = img_url if img_url else "https://cdn-icons-png.flaticon.com/512/3389/3389081.png"

                # Fiyat hala yoksa (Amazon bulamadıysa) simülasyon yap
                if not rec.get('Price'):
                    if rec.get('Book'):
                        seed_val = len(rec['Book']) + ord(rec['Book'][0])
                        random.seed(seed_val)
                        random_price = random.uniform(120, 550) # Yabancı kitaplar biraz daha pahalı olabilir
                        rec['Price'] = f"{random_price:.2f}"
                    else:
                        rec['Price'] = "199.90"

                # --- C. SEPET VE LİNK EŞLEŞTİRME ---
                rec['db_id'] = None
                rec['comment_url'] = None 
                
                # Veritabanında (Product tablosunda) İSİM ile ara
                if rec.get('Book'):
                    try:
                        db_product = Product.objects.filter(name__icontains=rec.get('Book')).first()
                        if db_product:
                            rec['db_id'] = db_product.id
                            rec['comment_url'] = db_product.external_url 
                    except:
                        pass
                
                # Veritabanında yoksa Pickle'dan gelen URL'yi kullan
                if not rec['comment_url']:
                     raw_url = rec.get('URL') or rec.get('external_url')
                     if raw_url and str(raw_url).startswith('http'):
                         rec['comment_url'] = raw_url

    context = {
        "book": book,
        "recommendations": recommendations,
        "query": query,
        "mode": mode
    }
    return render(request, "home.html", context)

def about(request): return render(request, 'about.html')
def contact(request):
    persons = person.objects.all()
    return render(request, 'contact.html', {'people': persons})