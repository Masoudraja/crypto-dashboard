import os
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv('COINGECKO_API_KEY')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# --- Top 50 Cryptocurrencies by Market Cap ---
# Start with top 50 for performance, can expand to 200 later
COINS_TO_TRACK = [
    'bitcoin', 'ethereum', 'ripple', 'tether', 'binancecoin', 'solana', 'usd-coin', 'dogecoin', 'staked-ether', 'tron',
    'cardano', 'wrapped-steth', 'chainlink', 'wrapped-beacon-eth', 'wrapped-bitcoin', 'hyperliquid', 'ethena-usde', 'sui', 'figure-heloc', 'avalanche-2',
    'wrapped-eeth', 'stellar', 'bitcoin-cash', 'weth', 'hedera-hashgraph', 'leo-token', 'litecoin', 'the-open-network', 'usds', 'crypto-com-chain',
    'shiba-inu', 'binance-bridged-usdt-bnb-smart-chain', 'coinbase-wrapped-btc', 'polkadot', 'whitebit', 'ethena-staked-usde', 'world-liberty-financial', 'monero', 'mantle', 'uniswap',
    'ethena', 'dai', 'pepe', 'aave', 'bitget-token', 'memecore', 'okb', 'jito-staked-sol', 'near', 'bittensor'
]

# --- API Configuration ---
COINGECKO_API_KEY = API_KEY
COINMARKETCAP_API_KEY = os.getenv('COINMARKETCAP_API_KEY')  # To be added
CRYPTOCOMPARE_API_KEY = os.getenv('CRYPTOCOMPARE_API_KEY')  # To be added
NEWS_API_KEY = os.getenv('NEWS_API_KEY')  # To be added

# --- Technical Indicators Configuration ---
INDICATORS_CONFIG = {
    'sma': [20, 50, 100, 200],  # Simple Moving Averages
    'ema': [12, 26, 50],        # Exponential Moving Averages
    'rsi': [14],                # RSI periods
    'macd': [(12, 26, 9)],      # MACD (fast, slow, signal)
    'bbands': [20],             # Bollinger Bands period
    'stoch_rsi': [14],          # Stochastic RSI
    'williams_r': [14],         # Williams %R
    'cci': [20],                # Commodity Channel Index
    'atr': [14],                # Average True Range
    'parabolic_sar': [(0.02, 0.2)],  # Parabolic SAR (acceleration, maximum)
    'ichimoku': [(9, 26, 52)]   # Ichimoku (conversion, base, lagging)
}