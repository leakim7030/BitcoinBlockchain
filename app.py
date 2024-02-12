import os
import requests
import schedule
import time

# Constants
UNCONFIRMED_TX_API_URL = "https://blockchain.info/unconfirmed-transactions?format=json"
WHALE_TRANSACTION_THRESHOLD = 10000000  # in satoshi (100 BTC)
SEND_DATA_INTERVAL = 15  # seconds
WORDPRESS_API_URL = "https://knudz.com/wp-json/blockchain/v1/data"
API_KEY = os.getenv('BLOCKCHAIN_API_KEY')

def fetch_unconfirmed_transactions():
    response = requests.get(UNCONFIRMED_TX_API_URL)
    response.raise_for_status()
    data = response.json()
    return data['txs']

def process_and_send_block_data():
    try:
        txs = fetch_unconfirmed_transactions()
        whale_transactions = [tx for tx in txs if sum(out['value'] for out in tx['out']) >= WHALE_TRANSACTION_THRESHOLD]

        # Sort whale transactions by total output in descending order and pick top 3
        top_3_whales = sorted(whale_transactions, key=lambda tx: sum(out['value'] for out in tx['out']), reverse=True)[:3]

        payload = {
            "whale_transactions_count": len(whale_transactions),
            "number_1_whale_transaction": top_3_whales[0] if len(top_3_whales) > 0 else None,
            "number_2_whale_transaction": top_3_whales[1] if len(top_3_whales) > 1 else None,
            "number_3_whale_transaction": top_3_whales[2] if len(top_3_whales) > 2 else None,
        }
        
        headers = {
            'X-WP-API-KEY': API_KEY,
            'Content-Type': 'application/json'
        }

        response = requests.post(WORDPRESS_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        print(f"Data sent successfully: {response.json()}")
    except requests.RequestException as e:
        print(f"Error fetching or sending data: {e}")

schedule.every(SEND_DATA_INTERVAL).seconds.do(process_and_send_block_data)

while True:
    try:
        schedule.run_pending()
        time.sleep(1)
    except Exception as e:
        print(f"Scheduling error: {e}")
        time.sleep(1)
