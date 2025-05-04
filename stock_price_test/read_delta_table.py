from pyspark.sql import SparkSession
from pyspark.sql.functions import col, date_trunc, avg, max, min
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MinIO configuration
MINIO_ENDPOINT = "http://localhost:9000"
MINIO_ACCESS_KEY = "minio"
MINIO_SECRET_KEY = "minio123"
MINIO_BUCKET = "stock-data"

# Delta Lake path
DELTA_PATH = f"s3a://{MINIO_BUCKET}/bitcoin_prices_delta"

def create_spark_session():
    """
    Create and configure Spark session with necessary dependencies for Delta Lake and MinIO
    """
    spark = (SparkSession.builder
        .appName("BitcoinPriceDeltaReader")
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

def read_bitcoin_data():
    """
    Read Bitcoin price data from Delta Lake format in MinIO
    """
    logger.info(f"Starting to read Bitcoin price data from {DELTA_PATH}...")
    
    # Create Spark session
    spark = create_spark_session()
    logger.info("Spark session created")
    
    try:
        # Read from Delta Lake
        df = spark.read.format("delta").load(DELTA_PATH)
        
        # Print schema and sample data
        logger.info("DataFrame schema:")
        df.printSchema()
        
        logger.info("Sample data:")
        df.show(10, truncate=False)
        
        # Count records
        count = df.count()
        logger.info(f"Total records read: {count}")
        
        # Basic analysis
        logger.info("Computing basic statistics...")
        
        # Daily statistics if timestamp is available
        if "timestamp" in df.columns:
            daily_stats = df.withColumn(
                "date", date_trunc("day", col("timestamp"))
            ).groupBy("date").agg(
                avg("vwap").alias("avg_price"),
                max("high").alias("max_price"),
                min("low").alias("min_price")
            ).orderBy("date")
            
            logger.info("Daily price statistics:")
            daily_stats.show(10)
        
        # Top 10 highest prices
        logger.info("Top 10 highest prices:")
        df.orderBy(col("vwap").desc()).select("timestamp", "vwap", "high", "low").show(10)
        
        # Create temporary view for SQL queries
        df.createOrReplaceTempView("bitcoin_prices")
        
        # Execute SQL query
        logger.info("SQL query results:")
        spark.sql("""
            SELECT 
                date_trunc('hour', timestamp) as hour,
                AVG(vwap) as avg_price,
                MAX(high) as max_price,
                MIN(low) as min_price
            FROM bitcoin_prices
            WHERE timestamp IS NOT NULL
            GROUP BY date_trunc('hour', timestamp)
            ORDER BY hour DESC
            LIMIT 24
        """).show()
        
    except Exception as e:
        logger.error(f"Error reading Bitcoin price data: {e}")
    finally:
        spark.stop()
        logger.info("Spark session stopped")

if __name__ == "__main__":
    read_bitcoin_data()