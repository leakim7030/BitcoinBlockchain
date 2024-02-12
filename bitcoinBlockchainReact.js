import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [transactionsData, setTransactionsData] = useState(null);
  const [whaleAlerts, setWhaleAlerts] = useState(null);

  useEffect(() => {
    // Fetch aggregated transactions data
    fetch('/api/transactions')
      .then(response => response.json())
      .then(data => setTransactionsData(data))
      .catch(error => console.error('Error fetching transactions data:', error));

    // Fetch whale alerts
    fetch('/api/whale-transactions')
      .then(response => response.json())
      .then(data => setWhaleAlerts(data))
      .catch(error => console.error('Error fetching whale alerts:', error));
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Bitcoin Blockchain Analyzer</h1>
        
        {transactionsData && (
          <div>
            <h2>Transactions Overview</h2>
            <p>Number of Transactions: {transactionsData.numberOfTransactions}</p>
            <p>Total Output (BTC): {transactionsData.totalOutputBTC}</p>
          </div>
        )}

        {whaleAlerts && (
          <div>
            <h2>Whale Alerts</h2>
            {whaleAlerts.whaleTransactions.map((transaction, index) => (
              <p key={index}>Hash: {transaction.hash}, Output: {transaction.totalOutputBTC} BTC</p>
            ))}
          </div>
        )}
      </header>
    </div>
  );
}

export default App;
