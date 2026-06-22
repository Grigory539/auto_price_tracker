"""
Load: Загрузка сырых данных из CSV в PostgreSQL
Загружает данные в таблицу staging_auto_prices (слой Staging)
"""

import csv
import json
from pathlib import Path
import psycopg2
from psycopg2 import sql, Error


import os

# Определяем окружение: если в Docker, используем имя сервиса PostgreSQL
if os.path.exists('/opt/airflow'):
    # Внутри Docker-контейнера Airflow
    DB_CONFIG = {
        'host': 'postgres',  # Имя сервиса из docker-compose.yml
        'port': 5432,
        'database': 'auto_tracker',
        'user': 'postgres',
        'password': 'postgres'
    }
else:
    # Локально на твоем компьютере
    DB_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'auto_tracker',
        'user': 'postgres',
        'password': 'postgres'
    }

# Путь к CSV-файлу
import os
if os.path.exists('/opt/airflow'):
    DATA_DIR = Path('/opt/airflow/data')
else:
    DATA_DIR = Path(__file__).parent.parent / 'data'
CSV_FILE = DATA_DIR / 'raw_prices.csv'


def load_to_staging():
    """Загружает данные из CSV в staging-таблицу"""
    
    print(f"{'='*60}")
    print(f"📥 Auto Price Tracker - Load")
    print(f"{'='*60}")
    print(f"Подключение к БД: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"База данных: {DB_CONFIG['database']}")
    print(f"Файл: {CSV_FILE}")
    print(f"{'='*60}\n")
    
    # Проверяем, что файл существует
    if not CSV_FILE.exists():
        print(f"❌ Файл не найден: {CSV_FILE}")
        print("   Сначала запусти extract.py")
        return False
    
    # Читаем CSV
    print("📖 Читаем CSV-файл...")
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        listings = list(reader)
    
    print(f"   ✅ Прочитано {len(listings)} записей")
    
    # Подключаемся к БД
    print("\n🔌 Подключаемся к PostgreSQL...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("   ✅ Подключение установлено")
    except Error as e:
        print(f"   ❌ Ошибка подключения: {e}")
        print("   Проверь, что PostgreSQL запущен: docker ps")
        return False
    
    try:
        # Очищаем staging перед загрузкой (чтобы не было дублей)
        print("\n🧹 Очищаем staging-таблицу...")
        cursor.execute("TRUNCATE TABLE staging_auto_prices RESTART IDENTITY;")
        conn.commit()
        print("   ✅ Таблица очищена")
        
        # Загружаем данные
        print("\n📤 Загружаем данные в staging_auto_prices...")
        
        insert_query = """
            INSERT INTO staging_auto_prices 
            (parsing_date, url, title, price_raw, year_raw, mileage_raw, city, seller_type, raw_json)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        loaded_count = 0
        for listing in listings:
            # Преобразуем все данные в строки для staging
            # (в staging храним "как есть", очистка будет в ODS)
            
            # Формируем JSON со всеми сырыми данными
            raw_json = json.dumps({
                'listing_id': listing['listing_id'],
                'url': listing['url'],
                'title': listing['title'],
                'year': listing['year'],
                'price': listing['price'],
                'mileage': listing['mileage'],
                'city': listing['city'],
                'seller_type': listing['seller_type'],
                'parsing_date': listing['parsing_date']
            }, ensure_ascii=False)
            
            cursor.execute(insert_query, (
                listing['parsing_date'],           # parsing_date
                listing['url'],                    # url
                listing['title'],                  # title
                str(listing['price']),             # price_raw (TEXT)
                str(listing['year']),              # year_raw (TEXT)
                str(listing['mileage']),           # mileage_raw (TEXT)
                listing['city'],                   # city
                listing['seller_type'],            # seller_type
                raw_json                           # raw_json (JSONB)
            ))
            loaded_count += 1
            
            # Логируем каждые 10 записей
            if loaded_count % 10 == 0:
                print(f"   Загружено {loaded_count}/{len(listings)} записей...")
        
        conn.commit()
        print(f"\n   ✅ Успешно загружено {loaded_count} записей")
        
        # Проверяем результат
        print("\n🔍 Проверяем результат...")
        cursor.execute("SELECT COUNT(*) FROM staging_auto_prices;")
        count = cursor.fetchone()[0]
        print(f"   В таблице staging_auto_prices: {count} записей")
        
        cursor.execute("""
            SELECT 
                MIN(price_raw::NUMERIC) as min_price,
                MAX(price_raw::NUMERIC) as max_price,
                AVG(price_raw::NUMERIC) as avg_price
            FROM staging_auto_prices;
        """)
        stats = cursor.fetchone()
        print(f"   Минимальная цена: {stats[0]:,.0f} руб.")
        print(f"   Максимальная цена: {stats[1]:,.0f} руб.")
        print(f"   Средняя цена: {stats[2]:,.0f} руб.")
        
    except Error as e:
        print(f"\n❌ Ошибка при загрузке: {e}")
        conn.rollback()
        return False
    
    finally:
        cursor.close()
        conn.close()
        print("\n🔌 Соединение с БД закрыто")
    
    print(f"\n{'='*60}")
    print(f"✅ Load завершен успешно!")
    print(f"{'='*60}")
    
    return True


if __name__ == '__main__':
    load_to_staging()