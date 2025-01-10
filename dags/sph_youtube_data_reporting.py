from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime, timedelta
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

# DAG configuration
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 8, 29),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'sph_youtube_data_reporting',
    default_args=default_args,
    description='A DAG to generate reports from processed YouTube data using Iceberg tables in Nessie',
    schedule_interval=timedelta(days=1),
)

# Define the path to your PySpark script
reporting_script_path = '/opt/airflow/scripts/spark_reporting_script.py'

# Define the SparkSubmitOperator to run the PySpark script
spark_reporting_task = SparkSubmitOperator(
    task_id='sph_generate_youtube_reports',
    application=reporting_script_path,
    name='youtube_data_reporting',
    conf={
        "spark.hadoop.fs.s3a.access.key": "admin",
        "spark.hadoop.fs.s3a.secret.key": "password",
        "spark.hadoop.fs.s3a.endpoint": "http://host.docker.internal:9000",
        "spark.hadoop.fs.s3a.connection.ssl.enabled": "false",
        "spark.hadoop.fs.s3a.path.style.access": "true",
        "spark.jars.packages": "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.2,"
                                "org.projectnessie.nessie-integrations:nessie-spark-extensions-3.5_2.12:0.95.0,"
                                "software.amazon.awssdk:bundle:2.20.131,"
                                "software.amazon.awssdk:url-connection-client:2.20.131,"
                                "org.apache.hadoop:hadoop-aws:3.3.1",
        "spark.sql.catalog.nessie": "org.apache.iceberg.spark.SparkCatalog",
        "spark.sql.catalog.nessie.uri": "http://host.docker.internal:19120/api/v1",
        "spark.sql.catalog.nessie.ref": "main",
        "spark.sql.catalog.nessie.authentication.type": "NONE",
        "spark.sql.catalog.nessie.warehouse": "s3a://reporting",
        "spark.sql.catalog.nessie.catalog-impl": "org.apache.iceberg.nessie.NessieCatalog",
        "spark.hadoop.fs.s3a.impl": "org.apache.hadoop.fs.s3a.S3AFileSystem",
    },
    verbose=True,
    env_vars={
        'JAVA_HOME': '/usr/lib/jvm/java-17-openjdk-arm64',
        'PATH': '/usr/lib/jvm/java-17-openjdk-arm64/bin:' + '/opt/spark/bin:' + '/opt/spark/sbin:' + '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
    },
    dag=dag,
)

# Set the task



######## Trigger Clear Landing files DAG ###################################

trigger_delete_landing_files_dag = TriggerDagRunOperator(
    task_id='trigger_delete_landing_files_dag',
    trigger_dag_id='clear_files_from_landing',  
    dag=dag,
)

spark_reporting_task >> trigger_delete_landing_files_dag
