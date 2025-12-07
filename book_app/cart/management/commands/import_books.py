# cart/management/commands/import_books.py

import csv
from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
from cart.models import Product # Product modelini kendi uygulamasından çekeriz

class Command(BaseCommand):
    help = 'CSV dosyasından kitap verilerini (Product) veritabanına aktarır.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Kitap verileri (Product) aktarılıyor..."))

        # DOSYA YOLU: BASE_DIR/data/books.csv olarak ayarlandı.
        csv_file_path = Path(settings.BASE_DIR) / 'data' / 'books.csv'
        
        if not csv_file_path.exists():
            self.stdout.write(self.style.ERROR(f"HATA: Dosya bulunamadı: {csv_file_path}"))
            self.stdout.write(self.style.ERROR("Lütfen dosya yolunu kontrol edin: data/books.csv"))
            return

        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            # CSV dosyasını okumak için DictReader kullanıyoruz
            reader = csv.DictReader(file)
            records_processed = 0
            records_skipped = 0

            for row in reader:
                try:
                    # CSV'deki sütun isimlerini (URL, Book, Author, Avg_Rating) kullanarak
                    # Product modelimizin alanlarına eşleştirme yapıyoruz:
                    book_data = {
                        'external_url': row['URL'], 
                        'name': row['Book'],
                        'author': row['Author'],
                        
                        # DÜZELTİLMİŞ KISIM: 'Avg_Rating' anahtarı kullanılıyor.
                        'average_rating': float(row['Avg_Rating']) if row.get('Avg_Rating') else None,
                    }
                    
                    # update_or_create ile dış kimliğe (external_url) göre eşleştirme ve kayıt/güncelleme
                    Product.objects.update_or_create(
                        external_url=book_data['external_url'], 
                        defaults=book_data
                    )
                    
                    records_processed += 1
                
                except Exception as e:
                    records_skipped += 1
                    self.stdout.write(self.style.WARNING(f"Hata! {row.get('Book', 'Bilinmeyen Kitap')}: {e}"))
            
            self.stdout.write(self.style.SUCCESS('--- AKTARIM TAMAMLANDI ---'))
            self.stdout.write(self.style.SUCCESS(f"Toplam İşlenen/Güncellenen Kayıt: {records_processed}"))
            self.stdout.write(self.style.WARNING(f"Atlanan Kayıt (Hata Nedeniyle): {records_skipped}"))