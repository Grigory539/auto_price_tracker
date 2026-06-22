"""
Extract: Получение данных о ценах автомобилей
Режимы работы:
- simulation: генерация реалистичных данных (по умолчанию)
- scraping: попытка парсинга auto.ru (может не работать из-за защиты)
"""

import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import time


# Конфигурация
import os
# Определяем окружение: если в Docker, используем /opt/airflow, иначе локально
if os.path.exists('/opt/airflow'):
    OUTPUT_DIR = Path('/opt/airflow/data')
else:
    OUTPUT_DIR = Path(__file__).parent.parent / 'data'
OUTPUT_FILE = OUTPUT_DIR / 'raw_prices.csv'

# Параметры поиска
SEARCH_CONFIG = {
    'brand': 'Toyota',
    'model': 'Camry',
    'region': 'moscow',
    'min_year': 2015,
    'max_year': 2023,
    'listings_count': 50  # Количество объявлений для генерации
}


def generate_realistic_listing(listing_id):
    """Генерирует реалистичное объявление о продаже автомобиля"""
    
    # Генерация года выпуска
    year = random.randint(SEARCH_CONFIG['min_year'], SEARCH_CONFIG['max_year'])
    
    # Генерация пробега (чем старше, тем больше пробег)
    age = 2024 - year
    base_mileage = age * 15000  # ~15к км в год
    mileage = base_mileage + random.randint(-5000, 10000)
    mileage = max(5000, mileage)  # Минимум 5000 км
    
    # Генерация цены (зависит от года и пробега)
    base_price = 2500000  # Базовая цена для новой Camry
    year_discount = (2024 - year) * 150000  # -150к за каждый год
    mileage_discount = (mileage / 100000) * 100000  # -100к за каждые 100к км
    price = base_price - year_discount - mileage_discount
    price = price + random.randint(-100000, 100000)  # Разброс ±100к
    price = max(800000, price)  # Минимум 800к
    
    # Генерация города
    cities = ['Москва', 'Санкт-Петербург', 'Казань', 'Екатеринбург', 'Новосибирск']
    city = random.choice(cities)
    
    # Тип продавца
    seller_types = ['Частное лицо', 'Автосалон', 'Автосалон']  # 2/3 — салоны
    seller_type = random.choice(seller_types)
    
    # URL (имитация)
    url = f"https://auto.ru/catalog/toyota/camry/{listing_id}/"
    
    return {
        'listing_id': listing_id,
        'url': url,
        'title': f"{SEARCH_CONFIG['brand']} {SEARCH_CONFIG['model']}, {year}",
        'year': year,
        'price': price,
        'mileage': mileage,
        'city': city,
        'seller_type': seller_type,
        'parsing_date': datetime.now().strftime('%Y-%m-%d')
    }


def extract_simulation():
    """Режим симуляции: генерирует реалистичные данные"""
    print("🎭 Режим симуляции: генерируем реалистичные данные...")
    
    listings = []
    for i in range(1, SEARCH_CONFIG['listings_count'] + 1):
        listing = generate_realistic_listing(i)
        listings.append(listing)
        print(f"  Сгенерировано объявление #{i}: {listing['title']} - {listing['price']:,} руб.")
    
    return listings


def extract_scraping():
    """
    Режим парсинга: пытается получить данные с auto.ru
    ВНИМАНИЕ: auto.ru имеет защиту от парсинга, этот режим может не работать
    """
    print("🕷️ Режим парсинга: пытаемся получить данные с auto.ru...")
    
    # Формируем URL поиска
    url = f"https://auto.ru/catalog/{SEARCH_CONFIG['brand'].lower()}/{SEARCH_CONFIG['model'].lower()}/"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Пытаемся найти объявления (структура может меняться!)
        listings = []
        # Здесь должен быть парсинг HTML, но auto.ru использует JavaScript
        # и динамическую загрузку, поэтому BeautifulSoup не подойдет
        
        print("⚠️ auto.ru использует JavaScript для загрузки данных.")
        print("   Для полноценного парсинга нужен Selenium + WebDriver.")
        print("   Переключаемся на режим симуляции...")
        
        return extract_simulation()
        
    except Exception as e:
        print(f"❌ Ошибка парсинга: {e}")
        print("   Переключаемся на режим симуляции...")
        return extract_simulation()


def save_to_csv(listings):
    """Сохраняет данные в CSV"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        if not listings:
            print("❌ Нет данных для сохранения")
            return
        
        writer = csv.DictWriter(f, fieldnames=listings[0].keys())
        writer.writeheader()
        writer.writerows(listings)
    
    print(f"\n✅ Данные сохранены в {OUTPUT_FILE}")
    print(f"   Всего записей: {len(listings)}")


def main(mode='simulation'):
    """Основная функция"""
    print(f"{'='*60}")
    print(f"🚗 Auto Price Tracker - Extract")
    print(f"{'='*60}")
    print(f"Марка: {SEARCH_CONFIG['brand']}")
    print(f"Модель: {SEARCH_CONFIG['model']}")
    print(f"Режим: {mode}")
    print(f"{'='*60}\n")
    
    if mode == 'scraping':
        listings = extract_scraping()
    else:
        listings = extract_simulation()
    
    save_to_csv(listings)
    
    print(f"\n{'='*60}")
    print(f"✅ Extract завершен успешно!")
    print(f"{'='*60}")
    
    return listings


if __name__ == '__main__':
    # Запуск в режиме симуляции (по умолчанию)
    main(mode='simulation')
    
    # Для попытки парсинга раскомментируй:
    # main(mode='scraping')