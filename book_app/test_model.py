import pandas as pd
import pickle
import os
from sklearn.metrics.pairwise import linear_kernel

# Renkli çıktılar için (Terminalde şık dursun)
class Renk:
    MOR = '\033[95m'
    YESIL = '\033[92m'
    SARI = '\033[93m'
    SON = '\033[0m'

def model_yukle():
    print("🧠 Model dosyaları yükleniyor, lütfen bekleyin...")
    try:
        # Dosyalar 'data' klasöründe olduğu için yolu belirtiyoruz
        books = pickle.load(open('data/books_processed.pkl', 'rb'))
        tfidf = pickle.load(open('data/tfidf_model.pkl', 'rb'))
        tfidf_matrix = pickle.load(open('data/tfidf_matrix.pkl', 'rb'))
        print(f"{Renk.YESIL}✅ Model başarıyla yüklendi!{Renk.SON}")
        return books, tfidf, tfidf_matrix
    except FileNotFoundError:
        print("❌ HATA: .pkl dosyaları bulunamadı! Önce 'model_egit.py' dosyasını çalıştırın.")
        exit()

def tavsiye_getir(query, books, tfidf, matrix):
    # 1. Kullanıcının girdiği cümleyi matematiksel vektöre çevir
    query_vec = tfidf.transform([query])
    
    # 2. Kosinüs benzerliğini hesapla (Senin cümlen ile 10.000 kitap arasındaki açı)
    cosine_sim = linear_kernel(query_vec, matrix)
    
    # 3. Skorları al ve sırala
    sim_scores = list(enumerate(cosine_sim[0]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    
    # 4. En iyi 5 sonucu al (0'dan 5'e kadar)
    sim_scores = sim_scores[0:5]
    
    # 5. Kitap indekslerini bul ve veriyi getir
    book_indices = [i[0] for i in sim_scores]
    return books.iloc[book_indices]

# --- ANA PROGRAM ---
if __name__ == "__main__":
    df, model, matris = model_yukle()
    
    print(f"\n{Renk.SARI}--- YAPAY ZEKA KİTAP DANIŞMANI ---{Renk.SON}")
    print("Çıkmak için 'q' yazın.\n")

    while True:
        user_input = input(f"{Renk.MOR}Ne tür bir kitap arıyorsunuz? (İngilizce tasvir edin): {Renk.SON}")
        
        if user_input.lower() == 'q':
            print("Görüşmek üzere!")
            break
        
        if len(user_input) < 3:
            print("Lütfen biraz daha detay verin...")
            continue
            
        # Tavsiyeleri al
        results = tavsiye_getir(user_input, df, model, matris)
        
        # Sonuçları ekrana bas
        print(f"\n--- '{user_input}' için Önerilerim ---")
        for index, row in results.iterrows():
            print(f"📖 {Renk.YESIL}{row['Book']}{Renk.SON} - {row['Author']}")
            print(f"   💰 Fiyat: {row['Price']} TL | ⭐ Puan: {row['Average Rating']}")
            print(f"   ℹ️  Özet: {str(row['Description'])[:100]}...") # Özetin ilk 100 karakteri
            print("-" * 40)
        print("\n")