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

def process_whale_transaction(tx):
    # Assuming the first input and output are representative for simplification
    from_address = tx['inputs'][0]['prev_out']['addr'] if 'addr' in tx['inputs'][0]['prev_out'] else 'Unknown'
    to_address = tx['out'][0]['addr'] if 'addr' in tx['out'][0] else 'Unknown'
    amount_sent = sum(out['value'] for out in tx['out']) / 1e8  # Convert from satoshi to BTC
    return {'from': from_address, 'to': to_address, 'amount': amount_sent}

def process_and_send_block_data():
    try:
        txs = fetch_unconfirmed_transactions()
        
        # Filter and process whale transactions
        whale_transactions = [tx for tx in txs if sum(out['value'] for out in tx['out']) >= WHALE_TRANSACTION_THRESHOLD]
        processed_whales = [process_whale_transaction(tx) for tx in whale_transactions]
        
        # Sort whale transactions by amount sent, descending
        sorted_whales = sorted(processed_whales, key=lambda tx: tx['amount'], reverse=True)[:3]
        
        # Calculate total output and transaction count
        total_output_btc = sum(sum(out['value'] for out in tx['out']) for tx in txs) / 1e8
        transaction_count = len(txs)
        
        payload = {
            "whale_transactions_count": len(whale_transactions),
            "transaction_count": transaction_count,
            "total_output_btc": total_output_btc,
            "top_whale_transactions": sorted_whales,
        }
        
        headers = {
            'X-WP-API-KEY': API_KEY,
            'Content-Type': 'application/json'
        }

        response = requests.post(WORDPRESS_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        print(f"Data sent successfully: {payload}")
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
