from django.http import HttpResponse
from django.shortcuts import render
from .models import person
from data_api.models import Book 
from cart.models import Product, UserPreference # UserPreference eklendi
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
        
        pool_size = 80 
        sim_scores = sorted(list(enumerate(cosine_sim[0])), key=lambda x: x[1], reverse=True)[0:pool_size]
        
        random.shuffle(sim_scores)
        selected_scores = sim_scores[:top_n]
        
        book_indices = [i[0] for i in selected_scores]
        return books_df.iloc[book_indices].fillna('').to_dict('records')
    except Exception as e:
        print(f"Öneri hatası: {e}")
        return []

def get_amazon_data(title):
    try:
        search_url = f"https://www.amazon.com.tr/s?k={quote(title)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.google.com/"
        }
        response = requests.get(search_url, headers=headers, timeout=4)
        if response.status_code != 200: return None

        soup = BeautifulSoup(response.text, "html.parser")
        results = soup.find_all("div", {"data-component-type": "s-search-result"})
        if not results: return None
            
        first_result = results[0]
        data = {}

        price_tag = first_result.find("span", class_="a-price")
        if price_tag:
            offscreen_price = price_tag.find("span", class_="a-offscreen")
            if offscreen_price:
                data['price'] = offscreen_price.get_text(strip=True).replace("TL", "").strip()
        
        img_tag = first_result.find("img", class_="s-image")
        if img_tag:
            data['image'] = img_tag.get('src')
        return data
    except:
        return None

# --- VIEW FONKSİYONLARI ---

def home(request):
    book = None
    recommendations = []      # Arama sonuçları
    personalized_products = [] # KİŞİSEL ÖNERİLER (Yeni eklendi)
    query = ""
    mode = "random"

    # 1. RASTGELE KİTAP (SOL KISIM - DAILY PICK)
    if Book.objects.count() > 0:
        try:
            random_id = random.choice(Book.objects.values_list("id", flat=True))
            url = f"http://127.0.0.1:8000/api/{random_id}"
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                book = response.json()
                if not book.get('image_url'):
                    amazon_data = get_amazon_data(book.get("title", ""))
                    if amazon_data:
                        if amazon_data.get('price'): book["price"] = amazon_data.get('price')
                        if amazon_data.get('image'): book["image_url"] = amazon_data.get('image')
        except: book = None 

    # 2. KİŞİSELLEŞTİRİLMİŞ ÖNERİLER (ORTA KISIM)
    if request.user.is_authenticated:
        try:
            pref, created = UserPreference.objects.get_or_create(user=request.user)
            if pref.interest_keywords:
                # 4 tane kişisel öneri çek
                personalized_products = get_ai_recommendations(pref.interest_keywords, top_n=4)
                
                # Bu öneriler için de Amazon/Fiyat/Resim verilerini hazırlayalım
                for p_rec in personalized_products:
                    p_amazon = get_amazon_data(p_rec['Book'])
                    p_rec['Price'] = None
                    if p_amazon:
                        if p_amazon.get('price'): p_rec['Price'] = p_amazon['price']
                        if p_amazon.get('image'): p_rec['Image_URL'] = p_amazon['image']
                    
                    if not p_rec.get('Image_URL'):
                        img = p_rec.get('Image-URL-M') or p_rec.get('image_url') or p_rec.get('Image_URL')
                        p_rec['Image_URL'] = img if img else "https://cdn-icons-png.flaticon.com/512/3389/3389081.png"

                    if not p_rec.get('Price'):
                        seed_val = len(p_rec['Book']) + ord(p_rec['Book'][0]) if p_rec.get('Book') else 42
                        random.seed(seed_val)
                        p_rec['Price'] = f"{random.uniform(120, 550):.2f}"

                    p_rec['db_id'] = None
                    p_rec['comment_url'] = None
                    if p_rec.get('Book'):
                        try:
                            db_p = Product.objects.filter(name__icontains=p_rec.get('Book')).first()
                            if db_p:
                                p_rec['db_id'] = db_p.id
                                p_rec['comment_url'] = db_p.external_url
                        except: pass
        except Exception as e:
            print(f"Kişiselleştirme hatası: {e}")

    # 3. YAPAY ZEKA ARAMA SONUÇLARI (ALT KISIM)
    if 'desc' in request.GET:
        query = request.GET.get('desc')
        if query and len(query) > 1:
            recommendations = get_ai_recommendations(query)
            mode = "search"
            
            for rec in recommendations:
                amazon_data = get_amazon_data(rec['Book'])
                rec['Price'] = None
                if amazon_data:
                    if amazon_data.get('price'): rec['Price'] = amazon_data['price']
                    if amazon_data.get('image'): rec['Image_URL'] = amazon_data['image']
                
                if not rec.get('Image_URL'):
                    img_url = rec.get('Image-URL-M') or rec.get('image_url') or rec.get('Image_URL')
                    rec['Image_URL'] = img_url if img_url else "https://cdn-icons-png.flaticon.com/512/3389/3389081.png"

                if not rec.get('Price'):
                    seed_val = len(rec['Book']) + ord(rec['Book'][0]) if rec.get('Book') else 42
                    random.seed(seed_val)
                    rec['Price'] = f"{random.uniform(120, 550):.2f}"

                rec['db_id'] = None
                rec['comment_url'] = None 
                if rec.get('Book'):
                    try:
                        db_product = Product.objects.filter(name__icontains=rec.get('Book')).first()
                        if db_product:
                            rec['db_id'] = db_product.id
                            rec['comment_url'] = db_product.external_url 
                    except: pass
                
                if not rec['comment_url']:
                     raw_url = rec.get('URL') or rec.get('external_url')
                     if raw_url and str(raw_url).startswith('http'):
                         rec['comment_url'] = raw_url

    context = {
        "book": book,
        "recommendations": recommendations,      # Arama sonuçları
        "personalized_products": personalized_products, # Kişisel öneriler
        "query": query,
        "mode": mode
    }
    return render(request, "home.html", context)

def about(request): return render(request, 'about.html')
def contact(request):
    persons = person.objects.all()
    return render(request, 'contact.html', {'people': persons})