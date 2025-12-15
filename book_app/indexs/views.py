from django.http import HttpResponse
from django.shortcuts import render
from .models import person
from data_api.models import Book
from cart.models import Product
import requests
import random
from bs4 import BeautifulSoup
from urllib.parse import quote

# --- AI KÜTÜPHANELERİ (YEREL MODEL) ---
import os
import pickle
import pandas as pd
from django.conf import settings
from sklearn.metrics.pairwise import linear_kernel

# --- YENİ AI SERVİSİ IMPORTU (HUGGING FACE) ---
from data_api.ai_service import get_remote_ai_recommendations

print("⏳ Yerel AI Modeli yükleniyor...")

BASE_DIR = settings.BASE_DIR
DATA_PATH = os.path.join(BASE_DIR, 'data')

try:
    books_df = pickle.load(open(os.path.join(DATA_PATH, 'books_processed.pkl'), 'rb'))
    tfidf_model = pickle.load(open(os.path.join(DATA_PATH, 'tfidf_model.pkl'), 'rb'))
    tfidf_matrix = pickle.load(open(os.path.join(DATA_PATH, 'tfidf_matrix.pkl'), 'rb'))
    print("✅ Yerel Model hazır!")
except Exception as e:
    print(f"❌ HATA: Yerel Model yüklenemedi. {e}")
    books_df = None


# --- YARDIMCI FONKSİYONLAR ---

def get_local_ai_recommendations(query, top_n=6):
    """Mevcut yerel TF-IDF modelini kullanır (Arama kutusu için)"""
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
    """
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

        # 1. FİYAT
        price_tag = first_result.find("span", class_="a-price")
        if price_tag:
            offscreen_price = price_tag.find("span", class_="a-offscreen")
            if offscreen_price:
                price_text = offscreen_price.get_text(strip=True).replace("TL", "").strip()
                data['price'] = price_text

        # 2. RESİM
        img_tag = first_result.find("img", class_="s-image")
        if img_tag:
            data['image'] = img_tag.get('src')

        return data

    except Exception as e:
        return None


# --- VIEW FONKSİYONLARI ---

def home(request):
    book = None
    recommendations = []  # Arama Sonuçları (Eski Model)
    hf_recommendations = []  # "Sizin İçin Seçtiklerimiz" (Yeni HF Modeli)
    query = ""
    mode = "random"

    # 1. RASTGELE KİTAP (SOL KISIM)
    if Book.objects.count() > 0:
        try:
            random_id = random.choice(Book.objects.values_list("id", flat=True))
            # Kendi iç API'sine istek atıyor
            url = f"http://127.0.0.1:8000/api/{random_id}"
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                book = response.json()
                if not book.get('image_url'):
                    amazon_data = get_amazon_data(book.get("title", ""))
                    if amazon_data:
                        if amazon_data.get('price'): book["price"] = amazon_data.get('price')
                        if amazon_data.get('image'): book["image_url"] = amazon_data.get('image')
            else:
                book = None
        except:
            book = None

        # 2. YAPAY ZEKA ÖNERİLERİ

    # DURUM A: Kullanıcı Arama Yaptıysa (ESKİ SİSTEM ÇALIŞIR)
    if 'desc' in request.GET:
        query = request.GET.get('desc')
        if query and len(query) > 1:
            # Yerel fonksiyonu çağır
            recommendations = get_local_ai_recommendations(query)
            mode = "search"

            for rec in recommendations:
                # Amazon Verisi
                amazon_data = get_amazon_data(rec['Book'])
                rec['Price'] = None

                if amazon_data:
                    if amazon_data.get('price'): rec['Price'] = amazon_data['price']
                    if amazon_data.get('image'): rec['Image_URL'] = amazon_data['image']

                # Fallback Resim
                if not rec.get('Image_URL'):
                    img_url = rec.get('Image-URL-M') or rec.get('image_url') or rec.get('Image_URL')
                    rec['Image_URL'] = img_url if img_url else "https://cdn-icons-png.flaticon.com/512/3389/3389081.png"

                # Fallback Fiyat
                if not rec.get('Price'):
                    if rec.get('Book'):
                        seed_val = len(rec['Book']) + ord(rec['Book'][0])
                        random.seed(seed_val)
                        random_price = random.uniform(120, 550)
                        rec['Price'] = f"{random_price:.2f}"
                    else:
                        rec['Price'] = "199.90"

                # DB Eşleşmesi
                rec['db_id'] = None
                rec['comment_url'] = None
                if rec.get('Book'):
                    try:
                        db_product = Product.objects.filter(name__icontains=rec.get('Book')).first()
                        if db_product:
                            rec['db_id'] = db_product.id
                            rec['comment_url'] = db_product.external_url
                    except:
                        pass

                if not rec['comment_url']:
                    raw_url = rec.get('URL') or rec.get('external_url')
                    if raw_url and str(raw_url).startswith('http'):
                        rec['comment_url'] = raw_url

    # DURUM B: Arama Yoksa - Kullanıcı Geçmişine Göre Öner (YENİ HUGGING FACE API)
    else:
        try:
            # Şimdilik sahte veri (Mock Data) - İleride veritabanından gelecek
            dummy_history = {
                "Harry Potter and the Sorcerer's Stone (Harry Potter (Paperback))": 10,
                "The Fellowship of the Ring (The Lord of the Rings, Part 1)": 8
            }

            # API Servisini Çağır
            raw_data = get_remote_ai_recommendations(user_history=dummy_history)

            # Gelen veriyi template formatına uydur
            for item in raw_data:
                rec_obj = {
                    'Book': item.get('title'),
                    'Author': item.get('author'),
                    'score': item.get('weighted_score'),
                    'Price': None,
                    'Image_URL': None,
                    'db_id': None,
                    'comment_url': None
                }

                # Amazon ile zenginleştir
                amazon_data = get_amazon_data(rec_obj['Book'])
                if amazon_data:
                    if amazon_data.get('price'): rec_obj['Price'] = amazon_data['price']
                    if amazon_data.get('image'): rec_obj['Image_URL'] = amazon_data['image']

                # Resim yoksa varsayılan
                if not rec_obj['Image_URL']:
                    rec_obj['Image_URL'] = "https://cdn-icons-png.flaticon.com/512/3389/3389081.png"

                # Fiyat yoksa varsayılan
                if not rec_obj['Price']:
                    rec_obj['Price'] = "189.90"

                # DB Eşleşmesi
                try:
                    db_product = Product.objects.filter(name__icontains=rec_obj['Book']).first()
                    if db_product:
                        rec_obj['db_id'] = db_product.id
                        rec_obj['comment_url'] = db_product.external_url
                except:
                    pass

                hf_recommendations.append(rec_obj)
        except Exception as e:
            print(f"HF Entegrasyon Hatası: {e}")

    context = {
        "book": book,
        "recommendations": recommendations,  # Search Sonuçları
        "hf_recommendations": hf_recommendations,  # YENİ API Sonuçları (Ana Sayfa)
        "query": query,
        "mode": mode
    }

    return render(request, "home.html", context)


def about(request): return render(request, 'about.html')


def contact(request):
    persons = person.objects.all()
    return render(request, 'contact.html', {'people': persons})