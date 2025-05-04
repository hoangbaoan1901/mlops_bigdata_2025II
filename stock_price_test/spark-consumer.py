from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType
from pyspark.sql.functions import from_json, col, current_timestamp
import logging
import os
import io

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

# Delta Lake output path - use local path for checkpoints to avoid S3 issues
DELTA_PATH = f"s3a://{MINIO_BUCKET}/bitcoin_prices_delta_rt"
LOCAL_CHECKPOINT_PATH = "/tmp/spark-checkpoints/bitcoin_prices"

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
        .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
        # Add more S3A configurations
        .config("spark.hadoop.fs.s3a.committer.magic.enabled", "false")
        .config("spark.hadoop.fs.s3a.committer.name", "directory")
        .config("spark.hadoop.fs.s3a.fast.upload", "true")
        .config("spark.sql.sources.commitProtocolClass", "org.apache.spark.sql.execution.datasources.SQLHadoopMapReduceCommitProtocol")
        .getOrCreate())
    
    return spark

def ensure_local_checkpoint_dir():
    """
    Create local checkpoint directory
    """
    try:
        if not os.path.exists(LOCAL_CHECKPOINT_PATH):
            os.makedirs(LOCAL_CHECKPOINT_PATH)
            logger.info(f"Created local checkpoint directory: {LOCAL_CHECKPOINT_PATH}")
        return True
    except Exception as e:
        logger.error(f"Error creating local checkpoint directory: {e}")
        return False

def ensure_minio_directories(spark):
    """
    Ensure MinIO bucket and delta directory exist
    """
    try:
        # Create a temp DataFrame to write to S3 to ensure the bucket and path exist
        df = spark.createDataFrame([("dummy",)], ["value"])
        
        # Write an empty DataFrame to the Delta path to initialize directories
        delta_path = DELTA_PATH + "/_placeholder"
        logger.info(f"Creating directory structure at: {delta_path}")
        
        # Write the DataFrame in append mode to create the directory structure
        df.write.format("delta").mode("append").save(delta_path)
        logger.info("Successfully created directory structure in MinIO")
        
        return True
    except Exception as e:
        logger.error(f"Error ensuring MinIO directories: {e}")
        return False

def process_bitcoin_data():
    """
    Process Bitcoin data from Kafka and write to Delta Lake format in MinIO
    """
    logger.info("Starting Bitcoin price consumer...")
    
    # Ensure local checkpoint directory exists
    if not ensure_local_checkpoint_dir():
        raise Exception("Failed to create local checkpoint directory")
    
    # Create Spark session
    spark = create_spark_session()
    logger.info("Spark session created")
    
    try:
        # Ensure MinIO directory structure exists
        if not ensure_minio_directories(spark):
            raise Exception("Failed to create MinIO directory structure")
        
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

        # Write to Delta Lake format in MinIO using local checkpoints
        delta_query = (parsed_stream
            .writeStream
            .format("delta")
            .outputMode("append")
            .option("checkpointLocation", LOCAL_CHECKPOINT_PATH)
            .start(DELTA_PATH))
        
        logger.info(f"Started writing to Delta Lake at {DELTA_PATH}")
        
        # Wait for the streaming query to terminate
        delta_query.awaitTermination()
        
    except Exception as e:
        logger.error(f"Error in Bitcoin price consumer: {e}")
        spark.stop()

if __name__ == "__main__":
    process_bitcoin_data()