from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'start_youtube_data_pipeline',
    default_args=default_args,
    description='A dummy DAG to start the YouTube data pipeline',
    schedule_interval=None,  # Manually triggered or scheduled as needed
    catchup=False,
)

start = DummyOperator(
    task_id='start',
    dag=dag,
)

######## Trigger Data Fetch DAG  ###################################

trigger_fetch_data_dag = TriggerDagRunOperator(
    task_id='trigger_fetch_data_dag',
    trigger_dag_id='sph_youtube_data_fetch_channel_wise',  # ID of the DAG to trigger
    dag=dag,
)

start >> trigger_fetch_data_dag
