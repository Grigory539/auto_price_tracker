-- ============================================================
-- Transform: Очистка данных и построение витрины аналитики
-- ============================================================

-- ============================================================
-- ШАГ 1: Очистка данных (Staging → ODS)
-- ============================================================

-- Очищаем ODS перед загрузкой
TRUNCATE TABLE ods_auto_prices RESTART IDENTITY;

-- Вставляем очищенные данные
INSERT INTO ods_auto_prices (
    parsing_date,
    url,
    title,
    brand,
    model,
    year,
    price_rub,
    mileage_km,
    city,
    seller_type
)
SELECT 
    parsing_date::DATE AS parsing_date,
    url,
    title,
    -- Извлекаем бренд из title (первое слово)
    SPLIT_PART(title, ' ', 1) AS brand,
    -- Извлекаем модель из title (второе слово)
    SPLIT_PART(title, ' ', 2) AS model,
    -- Приводим год к INTEGER
    year_raw::INTEGER AS year,
    -- Приводим цену к NUMERIC (убираем пробелы, если есть)
    REPLACE(price_raw, ' ', '')::NUMERIC(12, 2) AS price_rub,
    -- Приводим пробег к INTEGER
    mileage_raw::INTEGER AS mileage_km,
    city,
    seller_type
FROM staging_auto_prices
WHERE 
    -- Фильтруем некорректные данные
    price_raw IS NOT NULL 
    AND price_raw != ''
    AND year_raw IS NOT NULL
    AND year_raw != ''
    AND mileage_raw IS NOT NULL
    AND mileage_raw != ''
    -- Фильтруем аномалии (цена не может быть отрицательной или слишком большой)
    AND REPLACE(price_raw, ' ', '')::NUMERIC > 0
    AND REPLACE(price_raw, ' ', '')::NUMERIC < 10000000  -- Максимум 10 млн
    AND year_raw::INTEGER BETWEEN 1990 AND 2024
    AND mileage_raw::INTEGER >= 0
    AND mileage_raw::INTEGER < 1000000;  -- Максимум 1 млн км

-- Проверяем результат
SELECT 
    COUNT(*) AS total_cleaned,
    COUNT(DISTINCT city) AS unique_cities,
    COUNT(DISTINCT seller_type) AS unique_seller_types
FROM ods_auto_prices;


-- ============================================================
-- ШАГ 2: Построение витрины аналитики (ODS → Mart)
-- ============================================================

-- Очищаем витрину перед загрузкой
TRUNCATE TABLE mart_price_analytics RESTART IDENTITY;

-- Вставляем агрегированные данные
INSERT INTO mart_price_analytics (
    report_date,
    brand,
    model,
    avg_price,
    median_price,
    min_price,
    max_price,
    listings_count,
    avg_mileage_km
)
SELECT 
    CURRENT_DATE AS report_date,
    brand,
    model,
    -- Средняя цена
    ROUND(AVG(price_rub), 2) AS avg_price,
    -- Медианная цена (через PERCENTILE_CONT)
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_rub), 2) AS median_price,
    -- Минимальная цена
    MIN(price_rub) AS min_price,
    -- Максимальная цена
    MAX(price_rub) AS max_price,
    -- Количество объявлений
    COUNT(*) AS listings_count,
    -- Средний пробег
    ROUND(AVG(mileage_km)) AS avg_mileage_km
FROM ods_auto_prices
GROUP BY brand, model;

-- Проверяем результат
SELECT * FROM mart_price_analytics;


-- ============================================================
-- ШАГ 3: Продвинутая аналитика (бонус для собеседования)
-- ============================================================

-- 3.1: Рейтинг объявлений по цене (с оконными функциями)
SELECT 
    id,
    title,
    price_rub,
    mileage_km,
    city,
    -- Ранг по цене (самые дешевые = 1)
    RANK() OVER (ORDER BY price_rub ASC) AS price_rank,
    -- Процентиль (какой процент объявлений дешевле)
    PERCENT_RANK() OVER (ORDER BY price_rub) AS price_percentile,
    -- Отклонение от средней цены
    price_rub - AVG(price_rub) OVER () AS deviation_from_avg
FROM ods_auto_prices
ORDER BY price_rank
LIMIT 10;


-- 3.2: Анализ по городам (с CTE)
WITH city_stats AS (
    SELECT 
        city,
        COUNT(*) AS listings_count,
        ROUND(AVG(price_rub), 2) AS avg_price,
        ROUND(AVG(mileage_km)) AS avg_mileage,
        -- Доля от общего количества объявлений
        ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS market_share
    FROM ods_auto_prices
    GROUP BY city
)
SELECT 
    city,
    listings_count,
    avg_price,
    avg_mileage,
    market_share,
    -- Ранг города по средней цене
    RANK() OVER (ORDER BY avg_price DESC) AS price_rank
FROM city_stats
ORDER BY listings_count DESC;


-- 3.3: Поиск аномалий (выбросы цен)
WITH price_stats AS (
    SELECT 
        AVG(price_rub) AS avg_price,
        STDDEV(price_rub) AS stddev_price
    FROM ods_auto_prices
)
SELECT 
    o.id,
    o.title,
    o.price_rub,
    o.mileage_km,
    o.city,
    -- Z-score (сколько стандартных отклонений от среднего)
    ROUND((o.price_rub - ps.avg_price) / ps.stddev_price, 2) AS z_score
FROM ods_auto_prices o
CROSS JOIN price_stats ps
WHERE 
    -- Аномалии: цена отклоняется более чем на 2 стандартных отклонения
    ABS((o.price_rub - ps.avg_price) / ps.stddev_price) > 2
ORDER BY ABS((o.price_rub - ps.avg_price) / ps.stddev_price) DESC;


-- 3.4: Сравнение цен частников и салонов
SELECT 
    seller_type,
    COUNT(*) AS listings_count,
    ROUND(AVG(price_rub), 2) AS avg_price,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_rub), 2) AS median_price,
    MIN(price_rub) AS min_price,
    MAX(price_rub) AS max_price,
    ROUND(AVG(mileage_km)) AS avg_mileage
FROM ods_auto_prices
GROUP BY seller_type
ORDER BY avg_price DESC;