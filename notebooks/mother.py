from pyspark.sql import SparkSession

# MinIO connection details
MINIO_ACCESS_KEY = 'admin'
MINIO_SECRET_KEY = 'password'
MINIO_ENDPOINT = 'http://host.docker.internal:9000'

# Nessie connection details
NESSIE_URI = "http://host.docker.internal:19120/api/v1"
WAREHOUSE = "s3a://warehouse"

# Initialize Spark session with MinIO and Nessie configurations
spark = SparkSession.builder \
    .appName("MinIO_Nessie_Test") \
    .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY) \
    .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY) \
    .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT) \
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.jars.packages", 
            "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.2,"
            "org.projectnessie.nessie-integrations:nessie-spark-extensions-3.5_2.12:0.95.0,"
            "software.amazon.awssdk:bundle:2.20.131,"
            "software.amazon.awssdk:url-connection-client:2.20.131," "org.apache.hadoop:hadoop-aws:3.3.1") \
    .config("spark.sql.catalog.nessie", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.nessie.uri", NESSIE_URI) \
    .config("spark.sql.catalog.nessie.ref", "main") \
    .config("spark.sql.catalog.nessie.authentication.type", "NONE") \
    .config('spark.sql.catalog.nessie.warehouse', WAREHOUSE) \
    .config("spark.sql.catalog.nessie.catalog-impl", "org.apache.iceberg.nessie.NessieCatalog") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")  \
    .getOrCreate()



import os 
# MinIO connection details
MINIO_ACCESS_KEY = 'admin'
MINIO_SECRET_KEY = 'password'
MINIO_ENDPOINT = 'http://host.docker.internal:9000'


# Test connection to MinIO by reading a file
bucket_name = "landing"
object_key = "s3a://landing/Berita_Harian_Singapura_raw_data.json"
df = spark.read.json(object_key)
df.show()

# Example operation
try:
    spark.sql("CREATE TABLE nessie.names (name STRING) USING iceberg;").show()
except Exception as e:
    print(f"An error occurred: {e}")

# Stop the Spark session
spark.stop()
