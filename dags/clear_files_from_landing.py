from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import boto3
from botocore.client import Config

# Define default arguments for the DAG
default_args = {
    'owner': 'your_name',
    'depends_on_past': False,
    'start_date': datetime(2024, 8, 30),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# MinIO credentials and endpoint
bucket_name = 'landing'
minio_endpoint = 'http://host.docker.internal:9000'
minio_access_key = 'admin'
minio_secret_key = 'password'

# List of folders to clean up
folders = ['The Straits Times', 'The Business Times', 'zaobaosg', 'Tamil Murasu', 'Berita Harian']

# Function to delete all files from the specified folders in the landing bucket using boto3
def delete_files_from_landing(**kwargs):
    # Configure the boto3 client to connect to MinIO
    s3 = boto3.client(
        's3',
        endpoint_url=minio_endpoint,
        aws_access_key_id=minio_access_key,
        aws_secret_access_key=minio_secret_key,
        config=Config(signature_version='s3v4'),
        region_name='us-east-1'  # Region name can be anything
    )

    # Iterate over each folder and delete objects
    for folder in folders:
        prefix = f"{folder}/"  # Ensure the prefix ends with a '/'
        objects = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        
        if 'Contents' in objects:
            for obj in objects['Contents']:
                s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
                print(f"Deleted {obj['Key']} from {bucket_name}/{folder}")

# Define the DAG
with DAG(
    'clear_files_from_landing',
    default_args=default_args,
    description='Delete all files from landing bucket after YouTube data processing',
    schedule_interval=None,  # Trigger manually or via another DAG
    catchup=False,
) as dag:

    delete_landing_files = PythonOperator(
        task_id='delete_landing_files',
        python_callable=delete_files_from_landing,
        provide_context=True,
    )

    delete_landing_files
