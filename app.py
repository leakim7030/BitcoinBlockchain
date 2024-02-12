import os
import requests

import schedule
import time

# Constants
# Get the API key from environment variables
api_key = os.getenv('BLOCKCHAIN_API_KEY')
UNCONFIRMED_TRANSACTIONS_URL = "https://blockchain.info/unconfirmed-transactions?format=json"
WORDPRESS_API_URL = "https://knudz.com/wp-json/blockchain/v1/data"
WHALE_TRANSACTION_THRESHOLD = 100  # BTC
SEND_DATA_INTERVAL = 15  # seconds

def fetch_unconfirmed_transactions():
    try:
        response = requests.get(UNCONFIRMED_TRANSACTIONS_URL)
        response.raise_for_status()  # Raises an HTTPError if the response was an error
        data = response.json()
        return data['txs']
    except requests.RequestException as e:
        print(f"Error fetching unconfirmed transactions: {e}")
        return []

def process_and_send_data():
    try:
        unconfirmed_transactions = fetch_unconfirmed_transactions()
        whale_transactions = []
        for tx in unconfirmed_transactions:
            total_output = sum(output['value'] for output in tx['out']) / 1e8
            if total_output >= WHALE_TRANSACTION_THRESHOLD:
                whale_transactions.append({
                    "hash": tx['hash'],
                    "total_output": total_output,
                    "inputs": tx['inputs'],
                    "outputs": tx['out']
                })
        whale_transactions = sorted(whale_transactions, key=lambda x: x['total_output'], reverse=True)[:3]

        # Prepare data for sending
        payload = {
            "whale_transactions": whale_transactions,
            "total_transactions": len(unconfirmed_transactions)
        }

        # Append additional data for number 1 whale transaction
        if whale_transactions:
            payload["number_1_whale_transaction"] = {
                "hash": whale_transactions[0]["hash"],
                "amount_sent": whale_transactions[0]["total_output"],
                "timestamp": time.time()  # Assuming current timestamp
            }
        
        # Append additional data for number 2 and number 3 whale transactions
        if len(whale_transactions) > 1:
            payload["number_2_whale_transaction"] = {
                "hash": whale_transactions[1]["hash"],
                "amount_sent": whale_transactions[1]["total_output"],
                "timestamp": time.time()  # Assuming current timestamp
            }
        if len(whale_transactions) > 2:
            payload["number_3_whale_transaction"] = {
                "hash": whale_transactions[2]["hash"],
                "amount_sent": whale_transactions[2]["total_output"],
                "timestamp": time.time()  # Assuming current timestamp
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
schedule.every(SEND_DATA_INTERVAL).seconds.do(process_and_send_data)

# Run the scheduled task
while True:
    try:
        schedule.run_pending()
        time.sleep(1)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(1)
