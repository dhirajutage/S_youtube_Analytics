from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, year, month

# MinIO and Nessie connection details
MINIO_ACCESS_KEY = 'admin'
MINIO_SECRET_KEY = 'password'
MINIO_ENDPOINT = 'http://host.docker.internal:9000'
NESSIE_URI = "http://host.docker.internal:19120/api/v1"
WAREHOUSE = "s3a://curated"

# Initialize Spark session with MinIO and Nessie configurations
spark = SparkSession.builder \
    .appName("youtube_data_processing") \
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

# Create the Nessie table if it doesn't exist
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS nessie.youtube_video_data_tbl (
        channelName STRING,
        subscribers INT,
        totalVideos INT,
        video_title STRING,
        publishedAt TIMESTAMP,
        viewCount INT,
        year INT,
        month INT
    ) USING iceberg
    PARTITIONED BY (year, month)
    
""")

#######################################
#PARTITIONED BY (year, month);

#Dremio is taking too much time to process commenting

#######################################


# Truncate the table before inserting new data
#spark.sql("TRUNCATE TABLE nessie.youtube_video_data")

# Process each channel's data and write to a single table
for channel_name, object_key in channels.items():
    # Load the data from the landing bucket
    df = spark.read.json(object_key)

    # Explode the 'videos' array to work with individual video records
    df = df.withColumn("video", explode("videos"))
    
    # Extract and cast fields from the nested structure
    df = df.select(
        col("channelName"),
        col("subscribers").cast("int"),
        col("totalVideos").cast("int"),
        col("video.title").alias("video_title"),
        col("video.publishedAt").cast("timestamp").alias("publishedAt"),
        col("video.viewCount").cast("int"),
        year(col("video.publishedAt").cast("timestamp")).alias("year"),
        month(col("video.publishedAt").cast("timestamp")).alias("month")
    )
    
    # Insert data into the Nessie table with partitioning
    df.createOrReplaceTempView("video_data_temp")
    spark.sql(f"""
        INSERT INTO nessie.youtube_video_data_tbl
        SELECT * FROM video_data_temp
    """)

# Stop the Spark session
spark.stop()