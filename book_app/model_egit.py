import pandas as pd
import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

# 1. VERİYİ YÜKLE
print("Veri seti yükleniyor...")
try:
    # Hata veren satırları atla (on_bad_lines='skip')
    df = pd.read_csv('data/books.csv', on_bad_lines='skip')
    
    print(f"İlk yüklenen kitap sayısı: {len(df)}")

    # 2. SÜTUN İSİMLERİNİ DÜZENLEME
    # Senin verdiğin gerçek isimleri, projenin beklediği isimlere çeviriyoruz
    df.rename(columns={
        'Avg_Rating': 'Average Rating',   
        'Num_Ratings': 'Number of Ratings',
        'URL': 'Book_Link'                
    }, inplace=True)

    # 3. EKSİK VERİLERİ DOLDURMA (Simülasyon)
    
    

    df['Image_URL'] = "https://placehold.co/200x300?text=" + df['Book'].astype(str).str.slice(0, 20).str.replace(" ", "+")
    
    # Fiyat Yoksa: 50 TL ile 300 TL arası rastgele fiyat ata
    df['Price'] = np.random.uniform(50, 300, df.shape[0]).round(2)

    # Boş metin alanlarını doldur (Hata almamak için)
    df['Description'] = df['Description'].fillna('')
    df['Genres'] = df['Genres'].fillna('')
    df['Author'] = df['Author'].fillna('Bilinmiyor')

    # 4. ÖZELLİK MÜHENDİSLİĞİ (METİN HAVUZU OLUŞTURMA)
    # Modelin arama yapacağı tek bir büyük metin sütunu oluşturuyoruz
    def create_soup(x):
        
        genres = str(x['Genres']).replace("['", "").replace("']", "").replace("', '", " ")
        return f"{x['Book']} {x['Author']} {genres} {x['Description']}"

    df['soup'] = df.apply(create_soup, axis=1)

    # 5. MODELİ EĞİT (TF-IDF)
    print("Yapay zeka modeli eğitiliyor (Metinler işleniyor)...")
    
    # İngilizce stop words (ve, veya, bir gibi kelimeler) atılıyor
    tfidf = TfidfVectorizer(stop_words='english')
    
    # Tüm kitap özetleri sayısal matrise çevriliyor
    tfidf_matrix = tfidf.fit_transform(df['soup'])

    # 6. DOSYALARI KAYDET
    print("Dosyalar 'data/' klasörüne kaydediliyor...")
    
    # İşlenmiş veriyi kaydet (Fiyat ve Resim eklenmiş hali)
    pickle.dump(df, open('data/books_processed.pkl', 'wb'))
    
    # Modeli kaydet
    pickle.dump(tfidf, open('data/tfidf_model.pkl', 'wb'))
    
    # Matrisi kaydet
    pickle.dump(tfidf_matrix, open('data/tfidf_matrix.pkl', 'wb'))

    print("\n--- İŞLEM BAŞARILI! ---")
    print(f"Toplam {len(df)} kitap işlendi ve modele öğretildi.")
    print("Artık 'test_et.py' dosyasını çalıştırıp deneyebilirsin.")

except Exception as e:
    print(f"\nBİR HATA OLUŞTU: {e}")