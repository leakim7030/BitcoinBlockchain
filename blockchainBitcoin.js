require('dotenv').config();
const express = require('express');
const axios = require('axios');
const app = express();

const port = process.env.PORT || 3000; // Use environment variable for the port or default to 3000

app.get('/', (req, res) => {
  res.send('Bitcoin Blockchain Analyzer Backend is running. Use /api/transactions and /api/whale-transactions endpoints.');
});

// Function to fetch the latest block data
async function fetchLatestBlock() {
  try {
    const { data } = await axios.get('https://blockchain.info/latestblock');
    const blockDetails = await axios.get(`https://blockchain.info/rawblock/${data.hash}`);
    return blockDetails.data;
  } catch (error) {
    console.error('Error fetching blockchain data:', error);
    throw new Error('Failed to fetch blockchain data');
  }
}

// Function to find whale transactions and aggregate transactions data
async function analyzeBlockData(block, thresholdBTC = 100) { // Default threshold of 100 BTC for whale transactions
  let totalOutputBTC = 0;
  const whaleTransactions = [];

  block.tx.forEach(transaction => {
    const transactionTotalOutputBTC = transaction.out.reduce((acc, curr) => acc + curr.value, 0) / 100000000; // Convert from Satoshi to BTC
    totalOutputBTC += transactionTotalOutputBTC;

    if (transactionTotalOutputBTC >= thresholdBTC) {
      whaleTransactions.push({
        hash: transaction.hash,
        totalOutputBTC: transactionTotalOutputBTC,
      });
    }
  });

  return {
    numberOfTransactions: block.tx.length,
    totalOutputBTC,
    whaleTransactions,
  };
}

app.get('/api/transactions', async (req, res) => {
  try {
    const latestBlock = await fetchLatestBlock();
    const { numberOfTransactions, totalOutputBTC } = await analyzeBlockData(latestBlock);

    res.json({
      message: 'Aggregated transactions data from the latest block:',
      blockHash: latestBlock.hash,
      blockTime: new Date(latestBlock.time * 1000).toISOString(),
      numberOfTransactions,
      totalOutputBTC
    });
  } catch (error) {
    console.error('Error:', error.message);
    res.status(500).send('Error processing your request');
  }
});

app.get('/api/whale-transactions', async (req, res) => {
  try {
    const thresholdBTC = req.query.threshold ? parseFloat(req.query.threshold) : 100; // Allow threshold to be set via query parameter
    const latestBlock = await fetchLatestBlock();
    const { whaleTransactions } = await analyzeBlockData(latestBlock, thresholdBTC);

    res.json({
      message: `Whale transactions over ${thresholdBTC} BTC in the latest block:`,
      blockHash: latestBlock.hash,
      blockTime: new Date(latestBlock.time * 1000).toISOString(),
      whaleTransactionsCount: whaleTransactions.length,
      whaleTransactions
    });
  } catch (error) {
    console.error('Error:', error.message);
    res.status(500).send('Error processing your request');
  }
});

app.listen(port, () => {
  console.log(`Server listening at http://localhost:${port}`);
});
