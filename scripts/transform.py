"""
Transform: Выполнение SQL-трансформаций через psycopg2
Читает файл transform.sql и выполняет его в PostgreSQL
"""

from pathlib import Path
import psycopg2
from psycopg2 import Error


import os

if os.path.exists('/opt/airflow'):
    DB_CONFIG = {
        'host': 'postgres',
        'port': 5432,
        'database': 'auto_tracker',
        'user': 'postgres',
        'password': 'postgres'
    }
else:
    DB_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'auto_tracker',
        'user': 'postgres',
        'password': 'postgres'
    }

# Путь к SQL-файлу
SQL_FILE = Path(__file__).parent / 'transform.sql'


def run_transform():
    """Выполняет SQL-трансформации из файла transform.sql"""
    
    print(f"{'='*60}")
    print(f"🔄 Auto Price Tracker - Transform")
    print(f"{'='*60}")
    print(f"SQL-файл: {SQL_FILE}")
    print(f"{'='*60}\n")
    
    # Проверяем, что SQL-файл существует
    if not SQL_FILE.exists():
        print(f"❌ SQL-файл не найден: {SQL_FILE}")
        return False
    
    # Читаем SQL
    print("📖 Читаем SQL-файл...")
    with open(SQL_FILE, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    print(f"   ✅ Прочитано {len(sql_content)} символов SQL")
    
    # Подключаемся к БД
    print("\n🔌 Подключаемся к PostgreSQL...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("   ✅ Подключение установлено")
    except Error as e:
        print(f"   ❌ Ошибка подключения: {e}")
        return False
    
    try:
        # Разбиваем SQL на отдельные запросы по ';'
        # (psycopg2 не умеет выполнять несколько запросов за раз)
        print("\n⚙️ Выполняем SQL-трансформации...")
        
        # Разделяем SQL на отдельные команды
        queries = [q.strip() for q in sql_content.split(';') if q.strip() and not q.strip().startswith('--')]
        
        print(f"   Найдено {len(queries)} SQL-запросов для выполнения")
        
        for i, query in enumerate(queries, 1):
            # Пропускаем пустые и закомментированные запросы
            if not query or query.startswith('--'):
                continue
            
            try:
                cursor.execute(query)
                conn.commit()
                print(f"   ✅ Запрос {i} выполнен успешно")
            except Error as e:
                print(f"   ⚠️ Запрос {i}: {e}")
                # Не прерываем выполнение — некоторые запросы могут быть проверочными
        
        # Проверяем результат
        print("\n🔍 Проверяем результат...")
        
        cursor.execute("SELECT COUNT(*) FROM ods_auto_prices;")
        ods_count = cursor.fetchone()[0]
        print(f"   В ODS: {ods_count} очищенных записей")
        
        cursor.execute("SELECT COUNT(*) FROM mart_price_analytics;")
        mart_count = cursor.fetchone()[0]
        print(f"   В витрине: {mart_count} аналитических записей")
        
        if mart_count > 0:
            cursor.execute("""
                SELECT brand, model, avg_price, median_price, listings_count
                FROM mart_price_analytics
                LIMIT 1;
            """)
            result = cursor.fetchone()
            print(f"\n   📊 Пример из витрины:")
            print(f"      Бренд: {result[0]}")
            print(f"      Модель: {result[1]}")
            print(f"      Средняя цена: {result[2]:,.0f} руб.")
            print(f"      Медианная цена: {result[3]:,.0f} руб.")
            print(f"      Объявлений: {result[4]}")
        
    except Error as e:
        print(f"\n❌ Ошибка при выполнении: {e}")
        conn.rollback()
        return False
    
    finally:
        cursor.close()
        conn.close()
        print("\n🔌 Соединение с БД закрыто")
    
    print(f"\n{'='*60}")
    print(f"✅ Transform завершен успешно!")
    print(f"{'='*60}")
    
    return True


if __name__ == '__main__':
    run_transform()