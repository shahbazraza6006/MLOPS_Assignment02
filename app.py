import requests
from bs4 import BeautifulSoup
import csv
import re
import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator

def preprocess_text(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'[^a-zA-Z0-9\s-]', '', text)
    return text

def fetch_and_preprocess_data():
    url = "https://www.bbc.com/news"
    soup = BeautifulSoup(requests.get(url).content, "html.parser")
    headlines = soup.find_all("h2", class_="sc-4fedabc7-3 zTZri")
    descriptions = soup.find_all("p", class_="sc-b8778340-4 kYtujW")

    preprocessed_data = []
    for headline, description in zip(headlines, descriptions):
        preprocessed_headline = preprocess_text(headline.get_text(strip=True))
        preprocessed_description = preprocess_text(description.get_text(strip=True))
        preprocessed_data.append((preprocessed_headline, preprocessed_description))

    csv_file = "bbc_news_data.csv"
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Headline", "Description"])
        for headline, description in preprocessed_data:
            writer.writerow([headline, description])

    os.system("dvc add {}".format(csv_file))
    os.system("dvc push")

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 5, 12),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'bbc_news_dag',
    default_args=default_args,
    description='Fetch and preprocess BBC News data',
    schedule_interval=timedelta(days=1),
)

fetch_and_preprocess_task = PythonOperator(
    task_id='fetch_and_preprocess_task',
    python_callable=fetch_and_preprocess_data,
    dag=dag,
)

fetch_and_preprocess_task
