Структура проекта
auto-price-tracker/
├── dags/
│   └── auto_price_etl.py      # Airflow DAG
├── scripts/
│   ├── extract.py             # Сбор данных (симуляция)
│   ├── load.py                # Загрузка в staging
│   ├── transform.py           # Обёртка для SQL
│   ├── transform.sql          # SQL-трансформации
│   └── init.sql               # Создание таблиц
├── data/
│   └── raw_prices.csv         # Сырые данные
├── docker-compose.yml         # PostgreSQL + Airflow
├── requirements.txt           # Python-зависимости
└── README.md                  # Этот файл

------------------------------------------------------------

**Стек:**
- Python (psycopg2, pandas) — скрипты Extract и Load
- PostgreSQL 15 — база данных
- SQL — трансформации, оконные функции, CTE
- Apache Airflow — оркестрация DAG-ами
- Docker — контейнеры для PostgreSQL и Airflow

-----------------------------------------------------------

**Архитектура (классический ELT):**
auto.ru (источник)
↓
Python (Extract) — собирает данные
↓
PostgreSQL: staging_auto_prices — сырые данные "как есть"
↓
SQL (Transform) — очистка, приведение типов
↓
PostgreSQL: ods_auto_prices — очищенные данные
↓
SQL (Transform) — агрегация, аналитика
↓
PostgreSQL: mart_price_analytics — витрина с метриками

----------------------------------------------------------

**Что делает пайплайн:**
1. **Extract** — генерирует реалистичные данные о ценах Toyota Camry (подробнее про симуляцию ниже)
2. **Load** — загружает сырые данные в staging-таблицу
3. **Transform** — очищает данные, приводит типы, ищет аномалии через Z-score, строит витрину

----------------------------------------------------------

## Как запустить

# 1. Поднять контейнеры
docker compose up -d

# 2. Подождать, пока PostgreSQL и Airflow запустятся
# Airflow UI: http://localhost:8080 (логин/пароль: airflow/airflow)

# 3. Создать таблицы в БД (через DBeaver или psql)
# SQL-скрипт в scripts/init.sql

# 4. Запустить DAG в Airflow UI или вручную:
cd scripts
python extract.py
python load.py
python transform.py
