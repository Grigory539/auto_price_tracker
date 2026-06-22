"""
Auto Price Tracker ETL DAG
Автоматически запускает Extract → Load → Transform каждый день в 8:00
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys
from pathlib import Path

# Добавляем путь к скриптам, чтобы Airflow мог их импортировать
SCRIPTS_DIR = Path('/opt/airflow/scripts')
sys.path.insert(0, str(SCRIPTS_DIR))


# === Функции-обертки для Airflow ===

def run_extract(**kwargs):
    """Запускает скрипт extract.py"""
    print("🚀 Запуск Extract...")
    from extract import main as extract_main
    extract_main(mode='simulation')
    print("✅ Extract завершен")


def run_load(**kwargs):
    """Запускает скрипт load.py"""
    print("🚀 Запуск Load...")
    from load import load_to_staging
    success = load_to_staging()
    if not success:
        raise Exception("Load failed!")
    print("✅ Load завершен")


def run_transform(**kwargs):
    """Запускает скрипт transform.py"""
    print("🚀 Запуск Transform...")
    from transform import run_transform as transform_main
    success = transform_main()
    if not success:
        raise Exception("Transform failed!")
    print("✅ Transform завершен")


# === Определяем DAG ===

default_args = {
    'owner': 'grigory',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2024, 1, 1),
}

dag = DAG(
    'auto_price_etl',
    default_args=default_args,
    description='ETL-пайплайн для сбора и анализа цен на Toyota Camry с auto.ru',
    schedule_interval='0 8 * * *',  # Каждый день в 8:00
    catchup=False,                   # Не запускать пропущенные запуски
    tags=['auto', 'etl', 'toyota', 'camry'],
)


# === Определяем задачи ===

extract_task = PythonOperator(
    task_id='extract_prices',
    python_callable=run_extract,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_to_staging',
    python_callable=run_load,
    dag=dag,
)

transform_task = PythonOperator(
    task_id='transform_to_mart',
    python_callable=run_transform,
    dag=dag,
)


# === Определяем порядок выполнения ===

extract_task >> load_task >> transform_task