from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime, timedelta

# DAG configuration
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 8, 29),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'sph_youtube_data_processing',
    default_args=default_args,
    description='A DAG to process YouTube data and store it using Nessie and MinIO',
    schedule_interval=timedelta(days=1),
)

# Spark configurations
spark_conf = {
    'spark.hadoop.fs.s3a.access.key': 'admin',
    'spark.hadoop.fs.s3a.secret.key': 'password',
    'spark.hadoop.fs.s3a.endpoint': 'http://host.docker.internal:9000',
    'spark.hadoop.fs.s3a.connection.ssl.enabled': 'false',
    'spark.hadoop.fs.s3a.path.style.access': 'true',
    'spark.jars.packages': 'org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.2,'
                           'org.projectnessie.nessie-integrations:nessie-spark-extensions-3.5_2.12:0.95.0,'
                           'software.amazon.awssdk:bundle:2.20.131,'
                           'software.amazon.awssdk:url-connection-client:2.20.131,'
                           'org.apache.hadoop:hadoop-aws:3.3.1',
    'spark.sql.catalog.nessie': 'org.apache.iceberg.spark.SparkCatalog',
    'spark.sql.catalog.nessie.uri': 'http://host.docker.internal:19120/api/v1',
    'spark.sql.catalog.nessie.ref': 'main',
    'spark.sql.catalog.nessie.authentication.type': 'NONE',
    'spark.sql.catalog.nessie.warehouse': 's3a://curated',
    'spark.sql.catalog.nessie.catalog-impl': 'org.apache.iceberg.nessie.NessieCatalog',
}


#################################################################
#                SEPARATE  SPARK APP BY CHANNELWISE
#################################################################
# def analyze_channel_data_spark(channel_name):
#     """
#     This function will be executed as a Spark job.
#     """
#     # Path to the script or notebook that performs the analysis
#     script_path = '/opt/airflow/scripts/spark_analysis_script.py'

#     # Use SparkSubmitOperator to run the PySpark script
#     return SparkSubmitOperator(
#         task_id=f'analyze_{channel_name.replace(" ", "_")}_data',
#         application=script_path,
#         name=f'analyze_{channel_name.replace(" ", "_")}_data',
#         conf=spark_conf,
#         application_args=[channel_name],
#          verbose=True,
#         env_vars={
#             'JAVA_HOME': '/usr/lib/jvm/java-11-openjdk-arm64',
#             'PATH': '/usr/lib/jvm/java-11-openjdk-arm64/bin:' + '/opt/spark/bin:' + '/opt/spark/sbin:' + '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
#         },
#         dag=dag,
#     )
#################################################################

script_path = '/opt/airflow/scripts/spark_analysis_script.py'
# Define the Spark job in Airflow
spark_submit_task = SparkSubmitOperator(
    task_id='sph_process_youtube_data',
    application=script_path,  
    name='youtube_data_processing',
    conf=spark_conf,
    verbose=True,
    env_vars={
            'JAVA_HOME': '/usr/lib/jvm/java-17-openjdk-arm64',
            'PATH': '/usr/lib/jvm/java-17-openjdk-arm64/bin:' + '/opt/spark/bin:' + '/opt/spark/sbin:' + '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
        },
    dag=dag,
)


######## Trigger Reporting DAG  ###################################

trigger_sph_youtube_data_reporting_dag = TriggerDagRunOperator(
    task_id='trigger_sph_youtube_data_reporting_dag',
    trigger_dag_id='sph_youtube_data_reporting',  
    dag=dag,
)

spark_submit_task >> trigger_sph_youtube_data_reporting_dag
