from pyspark.sql import SparkSession
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('youtube_data_reporting')

# Configuration variables
MINIO_ACCESS_KEY = 'admin'
MINIO_SECRET_KEY = 'password'
MINIO_ENDPOINT = 'http://host.docker.internal:9000'
NESSIE_URI = "http://host.docker.internal:19120/api/v1"
REPORTING_BUCKET = "s3a://reporting"

# Initialize Spark session for the Reporting layer
spark = SparkSession.builder \
    .appName("youtube_data_reporting") \
    .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY) \
    .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY) \
    .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT) \
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.jars.packages", 
            "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.2,"
            "org.projectnessie.nessie-integrations:nessie-spark-extensions-3.5_2.12:0.95.0,"
            "software.amazon.awssdk:bundle:2.20.131,"
            "software.amazon.awssdk:url-connection-client:2.20.131,"
            "org.apache.hadoop:hadoop-aws:3.3.1") \
    .config("spark.sql.catalog.nessie", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.nessie.uri", NESSIE_URI) \
    .config("spark.sql.catalog.nessie.ref", "main") \
    .config("spark.sql.catalog.nessie.authentication.type", "NONE") \
    .config("spark.sql.catalog.nessie.warehouse", REPORTING_BUCKET) \
    .config("spark.sql.catalog.nessie.catalog-impl", "org.apache.iceberg.nessie.NessieCatalog") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")  \
    .getOrCreate()

logger.info("Spark session initialized successfully.")

# Load the curated data from the Curated layer Iceberg table
curated_table = "nessie.youtube_video_data_tbl"
df_curated = spark.read.format("iceberg").load(curated_table)
logger.info("Curated data loaded successfully.")

# Register the DataFrame as a temporary view for SQL processing
df_curated.createOrReplaceTempView("youtube_video_data")

# 1. Create a summary table for total subscribers per channel
spark.sql("""
    CREATE OR REPLACE TABLE nessie.youtube_channel_subscribers
    USING iceberg
    AS
    SELECT
        channelName,
        MAX(subscribers) AS totalSubscribers
    FROM
        youtube_video_data
    GROUP BY
        channelName
""")
logger.info("Subscribers summary table created successfully.")

# 2. Create a summary table for total video counts per channel
spark.sql("""
    CREATE OR REPLACE TABLE nessie.youtube_video_count
    USING iceberg
    AS
    SELECT
        channelName,
        COUNT(video_title) AS totalVideosPublished
    FROM
        youtube_video_data
    GROUP BY
        channelName
""")
logger.info("Video count summary table created successfully.")

# 3. Create a summary table for video publishing trends over the last 12 months
spark.sql("""
    CREATE OR REPLACE TABLE nessie.youtube_video_trend
    USING iceberg
    AS
    SELECT
        channelName,
        year,
        month,
        COUNT(video_title) AS monthlyVideosPublished
    FROM
        youtube_video_data
    GROUP BY
        channelName, year, month
""")
logger.info("Video trend summary table created successfully.")

# 4. Create a summary table for the most viewed videos
spark.sql("""
    CREATE OR REPLACE TABLE nessie.youtube_most_viewed_videos
    USING iceberg
    AS
    SELECT
        channelName,
        video_title,
        MAX(viewCount) AS totalViews
    FROM
        youtube_video_data
    GROUP BY
        channelName, video_title
    ORDER BY
        totalViews DESC
""")
logger.info("Most viewed videos summary table created successfully.")

# Stop the Spark session
spark.stop()
logger.info("Spark session stopped successfully.")
