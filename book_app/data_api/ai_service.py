import requests

# --- SENİN API ADRESİN BURAYA GİRİLDİ ---
API_URL = "https://tahaisler24-bitirme-projesi-oneri.hf.space"


def get_remote_ai_recommendations(user_history=None, book_name=None):
    """
    Hugging Face üzerindeki AI servisine istek atar.
    """
    recommendations = []

    try:
        # Senaryo 1: Kitap Detayına Göre (Sepet/Detay)
        if book_name:
            response = requests.get(
                f"{API_URL}/recommend_by_book",
                params={"book_name": book_name},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                recommendations = data.get('recommendations', [])

        # Senaryo 2: Kullanıcı Geçmişine Göre (Ana Sayfa)
        elif user_history:
            response = requests.post(
                f"{API_URL}/recommend_by_user_history",
                json={"history": user_history},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                recommendations = data.get('user_recommendations', [])

    except Exception as e:
        print(f"AI Servis Hatası (Hugging Face): {e}")
        return []

    return recommendations