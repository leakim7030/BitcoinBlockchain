import os
import requests
import redis
import json
import schedule
import time

# Initialize Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Constants
API_URL = "https://blockchain.info/unconfirmed-transactions?format=json"
WP_API_URL = "https://knudz.com/wp-json/blockchain/v1/data"
FETCH_INTERVAL = 10  # Fetch every 10 seconds to adhere to API's limit
PROCESS_INTERVAL = 15  # Process data every 15 seconds
WHALE_THRESHOLD = 100 * 10**8  # 100 BTC in Satoshi

def fetch_transactions():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()
        txs = data.get('txs', [])
        for tx in txs:
            tx_hash = tx.get('hash')
            if tx_hash:  # Store transaction with its hash as key
                redis_client.set(f"tx:{tx_hash}", json.dumps(tx), ex=120)  # Expire after 2 minutes
    except Exception as e:
        print(f"Error fetching transactions: {e}")

def process_transactions():
    tx_keys = redis_client.keys("tx:*")
    transactions = [json.loads(redis_client.get(k)) for k in tx_keys]
    
    # Calculate total_output_btc and transaction_count
    total_output_satoshi = sum(sum(out['value'] for out in tx['out']) for tx in transactions)
    total_output_btc = total_output_satoshi / 10**8  # Convert Satoshi to BTC
    transaction_count = len(transactions)
    
    # Identify top 3 whale transactions
    whale_transactions = sorted(
        [tx for tx in transactions if sum(out['value'] for out in tx['out']) >= WHALE_THRESHOLD],
        key=lambda tx: sum(out['value'] for out in tx['out']),
        reverse=True
    )[:3]
    
    # Extract necessary details from whale transactions
    top_whales = [{
        'from': tx['inputs'][0]['prev_out'].get('addr', 'Unknown'),
        'to': tx['out'][0].get('addr', 'Unknown'),
        'amount': sum(out['value'] for out in tx['out']) / 10**8  # Convert Satoshi to BTC
    } for tx in whale_transactions]

    # Prepare data payload
    data_payload = {
        'transaction_count': transaction_count,
        'total_output_btc': total_output_btc,
        'top_whale_transactions': top_whales,
    }

    # Send data to WordPress
    headers = {'X-WP-API-KEY': os.getenv('WP_API_KEY'), 'Content-Type': 'application/json'}
    try:
        response = requests.post(WP_API_URL, json=data_payload, headers=headers)
        print(f"Data sent to WordPress. Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"Error sending data to WordPress: {e}")

schedule.every(FETCH_INTERVAL).seconds.do(fetch_transactions)
schedule.every(PROCESS_INTERVAL).seconds.do(process_transactions)

while True:
    schedule.run_pending()
    time.sleep(1)
