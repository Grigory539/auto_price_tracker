CREATE SCHEMA IF NOT EXISTS auto_price_tracker;

-- Staging: сырые данные
CREATE TABLE IF NOT EXISTS auto_price_tracker.staging_auto_prices (
    id SERIAL PRIMARY KEY,
    parsing_date DATE,
    url TEXT,
    title TEXT,
    price_raw TEXT,           -- Строка, т.к. формат может быть разным
    year_raw TEXT,
    mileage_raw TEXT,
    city TEXT,
    seller_type TEXT,
    raw_json JSONB            -- Сохраняем весь JSON для отладки
);

-- ODS: очищенные данные
CREATE TABLE IF NOT EXISTS auto_price_tracker.ods_auto_prices (
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
CREATE TABLE IF NOT EXISTS auto_price_tracker.mart_price_analytics (
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