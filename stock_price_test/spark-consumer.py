from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType
from pyspark.sql.functions import from_json, col, current_timestamp
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Kafka configuration
KAFKA_TOPIC = "bitcoin-price"
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

# MinIO configuration
MINIO_ENDPOINT = "http://localhost:9000"
MINIO_ACCESS_KEY = "minio"
MINIO_SECRET_KEY = "minio123"
MINIO_BUCKET = "stock-data"

# Delta Lake output path
DELTA_PATH = f"s3a://{MINIO_BUCKET}/bitcoin_prices_delta"

# Define schema for the incoming JSON data
schema = StructType([
    StructField("symbol", StringType(), True),
    StructField("timestamp", StringType(), True),
    StructField("open", DoubleType(), True),
    StructField("high", DoubleType(), True),
    StructField("low", DoubleType(), True),
    StructField("close", DoubleType(), True),
    StructField("volume", DoubleType(), True),
    StructField("vwap", DoubleType(), True),
    StructField("trades", IntegerType(), True),
    StructField("fetch_time", StringType(), True)
])

def create_spark_session():
    """
    Create and configure Spark session with necessary dependencies for Delta Lake and MinIO
    """
    spark = (SparkSession.builder
        .appName("BitcoinPriceConsumer")
        .config("spark.jars.packages", 
                "io.delta:delta-spark_2.12:3.3.0,"
                "org.apache.hadoop:hadoop-aws:3.3.2")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .getOrCreate())
    
    return spark

def process_bitcoin_data():
    """
    Process Bitcoin data from Kafka and write to Delta Lake format in MinIO
    """
    logger.info("Starting Bitcoin price consumer...")
    
    # Create Spark session
    spark = create_spark_session()
    logger.info("Spark session created")
    
    try:
        # Read from Kafka
        kafka_stream = (spark
            .readStream
            .format("kafka")
            .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
            .option("subscribe", KAFKA_TOPIC)
            .option("startingOffsets", "latest")
            .load())
        
        logger.info("Kafka stream initialized")
        
        # Parse JSON data
        parsed_stream = (kafka_stream
            .selectExpr("CAST(value AS STRING)")
            .select(from_json(col("value"), schema).alias("data"))
            .select("data.*")
            .withColumn("processing_time", current_timestamp()))

        # --- Debug: Write to console ---
        console_query = (parsed_stream
            .writeStream
            .format("console")
            .outputMode("append")
            .start())
        
        logger.info("Started writing to console for debugging")
        # --- End Debug ---

        # Write to Delta Lake format in MinIO
        checkpoint_path = f"s3a://{MINIO_BUCKET}/checkpoints/bitcoin_prices"
        delta_query = (parsed_stream
            .writeStream
            .format("delta")
            .outputMode("append")
            .option("checkpointLocation", checkpoint_path)
            .start(DELTA_PATH))
        
        logger.info(f"Started writing to Delta Lake at {DELTA_PATH}")
        
        # Wait for the streaming query to terminate (or use awaitAnyTermination)
        # spark.streams.awaitAnyTermination() # Use this if you want the job to run until any stream stops
        delta_query.awaitTermination() # Keep original behavior for now
        
    except Exception as e:
        logger.error(f"Error in Bitcoin price consumer: {e}")
        spark.stop()

if __name__ == "__main__":
    process_bitcoin_data()