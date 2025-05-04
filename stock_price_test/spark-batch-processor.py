from pyspark.sql import SparkSession
from pyspark.sql.functions import explode, col, to_timestamp, lit
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# File paths and configuration
INPUT_JSON_PATH = "/home/hoangbaoan/repos/mlops_bigdata_2025II/stock_price_test/stock_price2.json"

# MinIO configuration
MINIO_ENDPOINT = "http://localhost:9000"
MINIO_ACCESS_KEY = "minio"
MINIO_SECRET_KEY = "minio123"
MINIO_BUCKET = "stock-data"

# Delta Lake output path
DELTA_PATH = f"s3a://{MINIO_BUCKET}/bitcoin_prices_delta"

def create_spark_session():
    """
    Create and configure Spark session with necessary dependencies for Delta Lake and MinIO
    """
    spark = (SparkSession.builder
        .appName("BitcoinPriceJSONToDelta")
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

def process_bitcoin_json():
    """
    Process Bitcoin data from JSON file and write to Delta Lake format in MinIO
    """
    logger.info(f"Starting to process Bitcoin price data from {INPUT_JSON_PATH}...")
    
    # Create Spark session
    spark = create_spark_session()
    logger.info("Spark session created")
    
    try:
        # Read the JSON file
        raw_df = spark.read.option("multiline", "true").json(INPUT_JSON_PATH)
        logger.info("JSON file loaded successfully")
        
        # Explode the bars array and add symbol column
        df = raw_df.select(explode(col("bars.BTC/USD")).alias("bar"))
        
        # Extract all fields from the nested structure
        df = df.select(
            lit("BTC/USD").alias("symbol"),
            to_timestamp(col("bar.t")).alias("timestamp"),
            col("bar.o").alias("open"),
            col("bar.h").alias("high"),
            col("bar.l").alias("low"),
            col("bar.c").alias("close"),
            col("bar.v").alias("volume"),
            col("bar.vw").alias("vwap"),
            col("bar.n").alias("trades")
        )
        
        # Show sample data
        logger.info("Transformed DataFrame structure:")
        df.printSchema()
        df.show(5)
        
        # Count records
        count = df.count()
        logger.info(f"Total records to write: {count}")
        
        # Write to Delta Lake format in MinIO
        df.write \
            .format("delta") \
            .mode("overwrite") \
            .save(DELTA_PATH)
        
        logger.info(f"Successfully wrote {count} records to Delta Lake at {DELTA_PATH}")
        
    except Exception as e:
        logger.error(f"Error processing Bitcoin price data: {e}")
    finally:
        spark.stop()
        logger.info("Spark session stopped")

if __name__ == "__main__":
    process_bitcoin_json()