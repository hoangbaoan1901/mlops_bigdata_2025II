import requests
import time
import json
from datetime import datetime
from kafka import KafkaProducer
import logging
from dotenv import load_dotenv
import os


load_dotenv(dotenv_path="/home/hoangbaoan/repos/mlops_bigdata_2025II/stock_price_test/.env")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Alpaca key and secret:
# ALPACA_KEY = os.getenv("ALPACA_KEY")
# ALPACA_SECRET = os.getenv("ALPACA_SECRET")

# Kafka configuration
KAFKA_TOPIC = "bitcoin-price"
KAFKA_BOOTSTRAP_SERVERS = ["localhost:9092"]
SYMBOL = "BTC/USD"  # Cryptocurrency to track
FETCH_INTERVAL = 60  # Time in seconds between fetches

def fetch_last_trade():
    """
    Fetches the latest BTC/USD bar data from Alpaca
    """
    url = f"https://data.alpaca.markets/v1beta3/crypto/us/latest/bars?symbols=BTC%2FUSD"

    headers = {
        "accept": "application/json"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Check if we have bar data for the symbol
        if "bars" in data and SYMBOL in data["bars"]:
            bar_data = data["bars"][SYMBOL]
            
            # Format the data we want to send to Kafka
            processed_data = {
                "symbol": SYMBOL,
                "timestamp": bar_data["t"],
                "open": bar_data["o"],
                "high": bar_data["h"],
                "low": bar_data["l"],
                "close": bar_data["c"],
                "volume": bar_data["v"],
                "vwap": bar_data["vw"],
                "trades": bar_data["n"],
                "fetch_time": datetime.now().isoformat()
            }
            
            logger.info(f"Fetched {SYMBOL} data: closing price ${bar_data['c']}")
            return processed_data
        else:
            logger.warning(f"No bar data returned for {SYMBOL}")
            return None
    except Exception as e:
        logger.error(f"Error fetching data from Alpaca API: {e}")
        return None

def create_kafka_producer():
    """
    Creates and returns a Kafka producer instance
    """
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        return producer
    except Exception as e:
        logger.error(f"Error creating Kafka producer: {e}")
        return None

def main():
    """
    Main function to run the cryptocurrency price producer
    """
    logger.info(f"Starting real-time cryptocurrency price producer for {SYMBOL}...")
    producer = create_kafka_producer()
    
    if not producer:
        logger.error("Failed to create Kafka producer. Exiting.")
        return
    
    try:
        while True:
            crypto_data = fetch_last_trade()
            
            if crypto_data:
                logger.info(f"Sending {SYMBOL} data to Kafka: ${crypto_data['close']}")
                producer.send(KAFKA_TOPIC, value=crypto_data)
            
            # Wait before the next fetch
            time.sleep(FETCH_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("Stopping cryptocurrency price producer...")
    finally:
        if producer:
            producer.close()

if __name__ == "__main__":
    main()