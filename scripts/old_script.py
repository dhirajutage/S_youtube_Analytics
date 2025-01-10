from pyspark.sql import SparkSession
from pyspark.sql.functions import col, substring

# MinIO and Nessie connection details
MINIO_ACCESS_KEY = 'admin'
MINIO_SECRET_KEY = 'password'
MINIO_ENDPOINT = 'http://host.docker.internal:9000'
NESSIE_URI = "http://host.docker.internal:19120/api/v1"
WAREHOUSE = "s3a://warehouse"

# Initialize Spark session with MinIO and Nessie configurations
spark = SparkSession.builder \
    .appName("youtube_data_processing_1") \
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
    .config("spark.sql.catalog.nessie.warehouse", WAREHOUSE) \
    .config("spark.sql.catalog.nessie.catalog-impl", "org.apache.iceberg.nessie.NessieCatalog") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")  \
    .getOrCreate()

# Define the channels and file paths
channels = {
    "The Straits Times": "s3a://landing/The_Straits_Times/The_Straits_Times_raw_data.json",
    "The Business Times": "s3a://landing/The_Business_Times/The_Business_Times_raw_data.json",
    "zaobaosg": "s3a://landing/zaobaosg/zaobaosg_raw_data.json",
    "Tamil Murasu": "s3a://landing/Tamil_Murasu/Tamil_Murasu_raw_data.json",
    "Berita Harian": "s3a://landing/Berita_Harian/Berita_Harian_raw_data.json"
}

# Process each channel's data
for channel_name, object_key in channels.items():
    # Load the data from the landing bucket
    df = spark.read.json(object_key)

    # Extract the required fields
    subscribers = df.select("subscribers").collect()[0]["subscribers"]
    total_videos = df.select("totalVideos").collect()[0]["totalVideos"]

    # Trend analysis
    trend_df = df.withColumn("publish_month", substring("publishedAt", 1, 7)) \
                 .groupBy("publish_month") \
                 .count() \
                 .orderBy("publish_month")

    # Most viewed videos
    most_viewed_videos_df = df.orderBy(col("viewCount").desc()).select("title", "viewCount", "publishedAt").limit(5)

    # Save the processed data to the Nessie catalog using Iceberg
    trend_df.write.mode("append").format("iceberg").save(f"nessie.{channel_name.replace(' ', '_')}_trend_data")
    most_viewed_videos_df.write.mode("append").format("iceberg").save(f"nessie.{channel_name.replace(' ', '_')}_most_viewed_videos")

    # Create a summary report for the channel
    report_data = {
        "channel_name": channel_name,
        "subscribers": subscribers,
        "total_videos": total_videos,
        "trend_data_table": f"nessie.{channel_name.replace(' ', '_')}_trend_data",
        "most_viewed_videos_table": f"nessie.{channel_name.replace(' ', '_')}_most_viewed_videos"
    }
    
    report_df = spark.createDataFrame([report_data])
    report_df.write.mode("append").format("iceberg").save(f"nessie.{channel_name.replace(' ', '_')}_report")

# Stop the Spark session
spark.stop()
