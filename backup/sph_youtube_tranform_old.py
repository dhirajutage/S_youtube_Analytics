from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime, timedelta

# DAG configuration
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 8, 27),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'youtube_data_analysis_with_spark',
    default_args=default_args,
    description='Analyze YouTube data using PySpark and store results in S3',
    schedule_interval=timedelta(days=1),
)

# DEFINE SENSITIVE VARIABLES
CATALOG_URI = "http://nessie:19120/api/v1"
WAREHOUSE = "s3://warehouse"
MINIO_ACCESS_KEY = 'admin'
MINIO_SECRET_KEY = 'password'

# Define the Spark configuration as a dictionary
spark_conf = {
    # 'spark.master': 'spark://172.24.0.7:7077',
    'spark.app.name': 'youtube_data_analysis',
    'spark.jars.packages': 'org.apache.iceberg:iceberg-spark-runtime-3.4_2.12:1.4.0,org.projectnessie.nessie-integrations:nessie-spark-extensions-3.5_2.12:0.77.1,io.delta:delta-core_2.12:2.3.0,org.apache.hadoop:hadoop-aws:3.3.1,com.amazonaws:aws-java-sdk-bundle:1.11.1026',
    'spark.sql.extensions': 'org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions,org.projectnessie.spark.extensions.NessieSparkSessionExtensions,io.delta.sql.DeltaSparkSessionExtension',
    'spark.sql.catalog.nessie': 'org.apache.iceberg.spark.SparkCatalog',
    'spark.sql.catalog.nessie.uri': CATALOG_URI,
    'spark.sql.catalog.nessie.ref': 'main',
    'spark.sql.catalog.nessie.authentication.type': 'NONE',
    'spark.sql.catalog.nessie.catalog-impl': 'org.apache.iceberg.nessie.NessieCatalog',
    'spark.sql.catalog.nessie.warehouse': WAREHOUSE,
    'spark.sql.catalog.nessie.io-impl': 'org.apache.iceberg.hadoop.HadoopFileIO',
    'spark.hadoop.fs.s3a.access.key': MINIO_ACCESS_KEY,
    'spark.hadoop.fs.s3a.secret.key': MINIO_SECRET_KEY,
    'spark.hadoop.fs.s3a.endpoint': 'http://host.docker.internal:9000',
    'spark.hadoop.fs.s3a.connection.ssl.enabled': 'false',
    'spark.hadoop.fs.s3a.path.style.access': 'true',

    # Optional: Specific landing bucket configuration
    'spark.hadoop.fs.s3a.landing.access.key': MINIO_ACCESS_KEY,
    'spark.hadoop.fs.s3a.landing.secret.key': MINIO_SECRET_KEY,
    'spark.hadoop.fs.s3a.landing.endpoint': 'http://host.docker.internal:9000',
    'spark.hadoop.fs.s3a.landing.connection.ssl.enabled': 'false',
    'spark.hadoop.fs.s3a.landing.path.style.access': 'true',
}


def analyze_channel_data_spark(channel_name):
    """
    This function will be executed as a Spark job.
    """
    # Path to the script or notebook that performs the analysis
    script_path = '/opt/airflow/scripts/spark_analysis_script.py'

    # Use SparkSubmitOperator to run the PySpark script
    return SparkSubmitOperator(
        task_id=f'analyze_{channel_name.replace(" ", "_")}_data',
        application=script_path,
        name=f'analyze_{channel_name.replace(" ", "_")}_data',
        conf=spark_conf,
        application_args=[channel_name],
         verbose=True,
        env_vars={
            'JAVA_HOME': '/usr/lib/jvm/java-11-openjdk-arm64',
            'PATH': '/usr/lib/jvm/java-11-openjdk-arm64/bin:' + '/opt/spark/bin:' + '/opt/spark/sbin:' + '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
        },
        dag=dag,
    )

# Define the task for each channel
channels = [
    "The Straits Times",
    "The Business Times",
    "zaobaosg",
    "Tamil Murasu",
    "Berita Harian Singapura"
]

for channel_name in channels:
    analyze_channel_data_spark(channel_name)
