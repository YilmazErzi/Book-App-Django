from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view

from data_api.serializer import BookSerializer
from data_api.models import Book
from rest_framework import status

# --- YENİ EKLENEN IMPORT ---
# Oluşturduğumuz servisten fonksiyonu çağırıyoruz
from data_api.ai_service import get_remote_ai_recommendations


# Create your views here.

@api_view(['GET'])
def book_list(request):
    books = Book.objects.all()
    serializer = BookSerializer(books, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def book(request, id):
    """
    Tek bir kitabın detayını getirir ve YENİ AI SİSTEMİ ile benzerlerini önerir.
    """
    try:
        # Kitabı veritabanından çek
        book_obj = Book.objects.get(pk=id)
        serializer = BookSerializer(book_obj)

        # Serializer verisini (JSON) bir değişkene alıp modifiye edeceğiz
        data = serializer.data

        # --- AI ENTEGRASYONU BAŞLANGIÇ ---
        try:
            # Kitap ismini alıyoruz (Modelinde title alanı olduğunu varsayıyoruz)
            book_title = book_obj.title

            # Hugging Face API servisine soruyoruz
            recommendations = get_remote_ai_recommendations(book_name=book_title)

            # Gelen önerileri API cevabına 'similar_books' anahtarıyla ekliyoruz
            data['similar_books'] = recommendations

        except Exception as e:
            # AI servisi hata verirse ana akış bozulmasın, sadece boş liste dönelim
            print(f"AI Entegrasyon Hatası (View): {e}")
            data['similar_books'] = []
        # --- AI ENTEGRASYONU BİTİŞ ---

        return Response(data)

    except Book.DoesNotExist:
        return Response({"error": "No matching records found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
def book_update(request, id):
    try:
        book = Book.objects.get(pk=id)
    except Book.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = BookSerializer(book, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def book_delete(request, id):
    try:
        book = Book.objects.get(pk=id)
        book.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Book.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def book_create(request):
    serializer = BookSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)