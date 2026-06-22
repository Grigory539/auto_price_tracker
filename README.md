# 🚗 Auto Price Tracker

ELT-пайплайн для мониторинга цен на автомобили с auto.ru. Автоматически собирает данные, очищает их и строит аналитическую витрину.

## 📌 Описание проекта

Проект демонстрирует построение полноценного ELT-процесса:
- **Extract:** Python-скрипт собирает данные о ценах на Toyota Camry
- **Load:** Загрузка сырых данных в PostgreSQL (слой Staging)
- **Transform:** SQL-трансформации для очистки данных и построения витрины (ODS → Mart)
- **Оркестрация:** Airflow DAG автоматизирует ежедневный запуск

## 🎯 Цель проекта

- Показать понимание архитектуры ELT с тремя слоями (Staging, ODS, Mart)
- Продемонстрировать работу с PostgreSQL, Python (pandas, psycopg2), Airflow
- Реализовать продвинутую SQL-аналитику: оконные функции, CTE, поиск аномалий
- Автоматизировать процесс через Airflow с мониторингом и retry

## 🛠 Технологический стек

- **Python:** pandas, psycopg2, requests, BeautifulSoup
- **PostgreSQL:** 15 (в Docker)
- **Apache Airflow:** 2.7.3 (оркестрация ETL)
- **Docker:** контейнеризация PostgreSQL и Airflow
- **SQL:** оконные функции, CTE, агрегации, поиск аномалий

## 📁 Структура проекта
auto-price-tracker/
├── dags/
│ └── auto_price_etl.py # Airflow DAG
├── scripts/
│ ├── extract.py # Python: Extract (симуляция парсинга)
│ ├── load.py # Python: Load (загрузка в staging)
│ ├── transform.py # Python: обертка для SQL
│ └── transform.sql # SQL: Transform (очистка + витрина)
├── data/
│ └── raw_prices.csv # Сырые данные (генерируются extract.py)
├── docker-compose.yml # PostgreSQL + Airflow в Docker
├── requirements.txt # Python-зависимости
└── README.md

## 🏗 Архитектура данных

┌─────────────┐ ┌──────────────┐ ┌─────────────┐
│ auto.ru │ ───▶ │ Python │ ───▶ │ PostgreSQL │
│ (источник) │ │ (Extract) │ │ (Staging) │
└─────────────┘ └──────────────┘ └──────┬──────┘
│
▼
┌──────────────┐
│ SQL │
│ (Transform) │
└──────┬───────┘
│
┌────────────────────┴────────────────────┐
▼ ▼
┌─────────────┐ ┌─────────────┐
│ ODS │ │ Mart │
│ (очищенные)│ │ (аналитика)│
└─────────────┘ └─────────────┘

## 🚀 Как запустить

### 1. Запусти Docker-контейнеры

docker compose up -d
Это запустит:
PostgreSQL на localhost:5432
Airflow Webserver на http://localhost:8080

2. Создай таблицы в PostgreSQL
Подключись к БД через DBeaver или psql и выполни:
-- Staging: сырые данные
CREATE TABLE IF NOT EXISTS staging_auto_prices (
    id SERIAL PRIMARY KEY,
    parsing_date DATE,
    url TEXT,
    title TEXT,
    price_raw TEXT,
    year_raw TEXT,
    mileage_raw TEXT,
    city TEXT,
    seller_type TEXT,
    raw_json JSONB
);

-- ODS: очищенные данные
CREATE TABLE IF NOT EXISTS ods_auto_prices (
    id SERIAL PRIMARY KEY,
    parsing_date DATE,
    url TEXT UNIQUE,
    title TEXT,
    brand VARCHAR(50),
    model VARCHAR(50),
    year INTEGER,
    price_rub NUMERIC(12, 2),
    mileage_km INTEGER,
    city VARCHAR(100),
    seller_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mart: витрина с аналитикой
CREATE TABLE IF NOT EXISTS mart_price_analytics (
    id SERIAL PRIMARY KEY,
    report_date DATE,
    brand VARCHAR(50),
    model VARCHAR(50),
    avg_price NUMERIC(12, 2),
    median_price NUMERIC(12, 2),
    min_price NUMERIC(12, 2),
    max_price NUMERIC(12, 2),
    listings_count INTEGER,
    avg_mileage_km INTEGER
);

3. Запусти ETL-пайплайн
Вариант А: Через Airflow UI
Открой http://localhost:8080
Войди: airflow / airflow
Найди DAG auto_price_etl
Нажми ▶️ (Play) → "Trigger DAG"
Вариант Б: Вручную через терминал

python extract.py      # Генерация данных
python load.py         # Загрузка в staging
python transform.py    # Очистка и построение витрины

4. Проверь результат
-- Посмотри витрину с аналитикой
SELECT * FROM mart_price_analytics;

-- Посмотри очищенные данные
SELECT * FROM ods_auto_prices LIMIT 10;

📊 Что получилось
Витрина аналитики (mart_price_analytics):
Средняя цена Toyota Camry
Медианная цена (устойчива к выбросам)
Минимальная и максимальная цена
Количество объявлений
Средний пробег
Продвинутая аналитика (в transform.sql):
Ранжирование объявлений по цене (оконные функции RANK, PERCENT_RANK)
Анализ по городам с долей рынка (CTE)
Поиск аномалий через Z-score (статистический метод)
Сравнение сегментов (частники vs салоны)

💡 Особенности реализации

1. Режим симуляции данных
Auto.ru имеет защиту от парсинга (Cloudflare, капча). Для демонстрации ETL-процесса используется режим симуляции, который генерирует реалистичные данные. В production-версии можно добавить Selenium + ротацию прокси.

2. Три слоя данных (ELT-архитектура)
Staging: сырые данные "как есть" (TEXT) — для аудита и отладки
ODS: очищенные данные с правильными типами — для аналитики
Mart: агрегированная витрина — для бизнес-отчетов

3. Автоматизация через Airflow
DAG запускается ежедневно в 8:00. Настроены:
Retry при ошибках (1 попытка через 5 минут)
Логирование каждого этапа
Мониторинг через Airflow UI

👤 Автор
Григорий Якульский
GitHub: https://github.com/Grigory539
Email: grigory234@yandex.ru
📝 Лицензия
Учебный проект. Свободное использование.