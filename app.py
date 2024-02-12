import os
import requests


import schedule
import time

# Constants
# Get the API key from environment variables
api_key = os.getenv('BLOCKCHAIN_API_KEY')
BLOCKCHAIN_INFO_API_URL = "https://blockchain.info/latestblock"
WHALE_TRANSACTION_THRESHOLD = 100  # BTC
SEND_DATA_INTERVAL = 15  # seconds
WORDPRESS_API_URL = "https://knudz.com/wp-json/blockchain/v1/data"

def fetch_latest_block_hash():
    response = requests.get(BLOCKCHAIN_INFO_API_URL)
    response.raise_for_status()  # Raises an HTTPError if the response was an error
    data = response.json()
    return data['hash']

def fetch_block_data(block_hash):
    block_data_url = f"https://blockchain.info/rawblock/{block_hash}"
    response = requests.get(block_data_url)
    response.raise_for_status()
    return response.json()

def process_and_send_block_data():
    try:
        latest_block_hash = fetch_latest_block_hash()
        block_data = fetch_block_data(latest_block_hash)
        
        # Process data
        whale_transactions = [tx for tx in block_data['tx'] if sum(out['value'] for out in tx['out']) / 1e8 >= WHALE_TRANSACTION_THRESHOLD]
        transaction_count = len(block_data['tx'])
        total_output_btc = sum(sum(out['value'] for out in tx['out']) for tx in block_data['tx']) / 1e8
        
        # Prepare data for sending
        payload = {
            "block_hash": latest_block_hash,
            "whale_transactions_count": len(whale_transactions),
            "transaction_count": transaction_count,
            "total_output_btc": total_output_btc,
        }
        
        headers = {
            'X-WP-API-KEY': api_key
        }

        response = requests.post(WORDPRESS_API_URL, json=payload, headers=headers)
        response.raise_for_status()  # Check for HTTP request errors
        print(f"Data sent successfully: {payload}")
    except requests.RequestException as e:
        print(f"Error fetching or sending data: {e}")

# Schedule the task
schedule.every(SEND_DATA_INTERVAL).seconds.do(process_and_send_block_data)

# Run the scheduled task
while True:
    try:
        schedule.run_pending()
        time.sleep(1)
    except Exception as e:
        print(f" error: {e}")
        time.sleep(1)
        pass 
