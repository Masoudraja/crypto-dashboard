#!/usr/bin/env python3
"""
Enhanced Data Sources Integration
Integrates multiple cryptocurrency APIs for comprehensive market analysis
"""

import requests
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from config import (
    COINGECKO_API_KEY, 
    COINMARKETCAP_API_KEY, 
    CRYPTOCOMPARE_API_KEY,
    COINS_TO_TRACK
)

class CryptoDataSources:
    """Comprehensive cryptocurrency data aggregation from multiple sources"""
    
    def __init__(self):
        self.coingecko_key = COINGECKO_API_KEY
        self.coinmarketcap_key = COINMARKETCAP_API_KEY
        self.cryptocompare_key = CRYPTOCOMPARE_API_KEY
        self.rate_limit_delay = 1  # seconds between API calls
    
    def fetch_coinmarketcap_data(self, symbols: List[str]) -> Dict[str, Any]:
        """Fetch data from CoinMarketCap API"""
        if not self.coinmarketcap_key:
            print("⚠️  CoinMarketCap API key not configured")
            return {}
        
        try:
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
            headers = {
                'X-CMC_PRO_API_KEY': self.coinmarketcap_key,
                'Accept': 'application/json'
            }
            
            # Convert coin IDs to symbols (CMC uses symbols, not IDs)
            symbol_mapping = {
                'bitcoin': 'BTC', 'ethereum': 'ETH', 'ripple': 'XRP',
                'cardano': 'ADA', 'solana': 'SOL', 'dogecoin': 'DOGE',
                'chainlink': 'LINK', 'polkadot': 'DOT', 'litecoin': 'LTC'
            }
            
            # Get symbols for first 10 coins (CMC has request limits)
            mapped_symbols = []
            for coin_id in symbols[:10]:
                if coin_id in symbol_mapping:
                    mapped_symbols.append(symbol_mapping[coin_id])
            
            if not mapped_symbols:
                return {}
            
            params = {
                'symbol': ','.join(mapped_symbols),
                'convert': 'USD'
            }
            
            print(f"📊 Fetching CoinMarketCap data for {len(mapped_symbols)} coins...")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status', {}).get('error_code') == 0:
                print(f"✅ CoinMarketCap data fetched successfully")
                return data.get('data', {})
            else:
                print(f"❌ CoinMarketCap API error: {data.get('status', {}).get('error_message')}")
                return {}
                
        except Exception as e:
            print(f"❌ Error fetching CoinMarketCap data: {e}")
            return {}
    
    def fetch_cryptocompare_social_data(self, coin_symbol: str) -> Dict[str, Any]:
        """Fetch social sentiment data from CryptoCompare"""
        if not self.cryptocompare_key:
            print("⚠️  CryptoCompare API key not configured")
            return {}
        
        try:
            url = f"https://min-api.cryptocompare.com/data/social/coin/histo/day"
            params = {
                'coinId': coin_symbol.upper(),
                'api_key': self.cryptocompare_key,
                'limit': 7  # Last 7 days
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('Response') == 'Success':
                return data.get('Data', {})
            else:
                print(f"❌ CryptoCompare API error: {data.get('Message')}")
                return {}
                
        except Exception as e:
            print(f"❌ Error fetching CryptoCompare data for {coin_symbol}: {e}")
            return {}
    
    def fetch_fear_greed_index(self) -> Dict[str, Any]:
        """Fetch Crypto Fear & Greed Index"""
        try:
            url = "https://api.alternative.me/fng/?limit=30"  # Last 30 days
            
            print("😨 Fetching Fear & Greed Index...")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('metadata', {}).get('error'):
                print(f"❌ Fear & Greed API error: {data['metadata']['error']}")
                return {}
            
            print("✅ Fear & Greed Index fetched successfully")
            return data.get('data', [])
            
        except Exception as e:
            print(f"❌ Error fetching Fear & Greed Index: {e}")
            return {}
    
    def fetch_enhanced_market_data(self, coin_ids: List[str]) -> Dict[str, Any]:
        """Fetch comprehensive market data from multiple sources"""
        enhanced_data = {}
        
        print(f"🚀 Fetching enhanced market data for {len(coin_ids)} cryptocurrencies...")
        
        # 1. Primary data from CoinGecko (already implemented in main.py)
        print("📈 Primary data source: CoinGecko")
        
        # 2. Additional metrics from CoinMarketCap
        cmc_data = self.fetch_coinmarketcap_data(coin_ids)
        
        # 3. Fear & Greed Index
        fear_greed_data = self.fetch_fear_greed_index()
        
        # 4. Social sentiment (for major coins)
        major_coins = ['BTC', 'ETH', 'ADA', 'SOL']  # Limit to avoid rate limits
        social_data = {}\n        for symbol in major_coins:\n            social_data[symbol] = self.fetch_cryptocompare_social_data(symbol)\n            time.sleep(self.rate_limit_delay)\n        \n        # Combine all data sources\n        enhanced_data = {\n            'coinmarketcap': cmc_data,\n            'fear_greed_index': fear_greed_data,\n            'social_sentiment': social_data,\n            'timestamp': datetime.now().isoformat()\n        }\n        \n        print(f\"✅ Enhanced market data compilation complete!\")\n        return enhanced_data\n    \n    def get_market_analysis_summary(self, enhanced_data: Dict[str, Any]) -> Dict[str, Any]:\n        \"\"\"Generate market analysis summary from multiple data sources\"\"\"\n        summary = {\n            'market_sentiment': 'neutral',\n            'fear_greed_score': None,\n            'social_activity': {},\n            'market_dominance': {},\n            'analysis_timestamp': datetime.now().isoformat()\n        }\n        \n        try:\n            # Analyze Fear & Greed Index\n            if enhanced_data.get('fear_greed_index'):\n                latest_fg = enhanced_data['fear_greed_index'][0]\n                score = int(latest_fg.get('value', 50))\n                summary['fear_greed_score'] = score\n                \n                if score <= 25:\n                    summary['market_sentiment'] = 'extreme_fear'\n                elif score <= 45:\n                    summary['market_sentiment'] = 'fear'\n                elif score <= 55:\n                    summary['market_sentiment'] = 'neutral'\n                elif score <= 75:\n                    summary['market_sentiment'] = 'greed'\n                else:\n                    summary['market_sentiment'] = 'extreme_greed'\n            \n            # Analyze CoinMarketCap data for market dominance\n            if enhanced_data.get('coinmarketcap'):\n                cmc_data = enhanced_data['coinmarketcap']\n                for symbol, data in cmc_data.items():\n                    if 'quote' in data and 'USD' in data['quote']:\n                        quote = data['quote']['USD']\n                        summary['market_dominance'][symbol] = {\n                            'market_cap_dominance': quote.get('market_cap_dominance'),\n                            'volume_24h': quote.get('volume_24h'),\n                            'percent_change_7d': quote.get('percent_change_7d')\n                        }\n            \n            # Analyze social sentiment\n            social_summary = {}\n            for symbol, data in enhanced_data.get('social_sentiment', {}).items():\n                if data and 'Data' in data:\n                    latest_social = data['Data'][-1] if data['Data'] else {}\n                    social_summary[symbol] = {\n                        'reddit_posts': latest_social.get('reddit', {}).get('posts_per_day', 0),\n                        'twitter_followers': latest_social.get('twitter', {}).get('followers', 0),\n                        'social_score': latest_social.get('overview_page_views', 0)\n                    }\n            summary['social_activity'] = social_summary\n            \n        except Exception as e:\n            print(f\"⚠️  Error analyzing market data: {e}\")\n        \n        return summary\n\n# Example usage\nif __name__ == \"__main__\":\n    print(\"🔍 Testing Enhanced Data Sources Integration\")\n    print(\"=\" * 60)\n    \n    data_sources = CryptoDataSources()\n    \n    # Test with a small subset\n    test_coins = COINS_TO_TRACK[:5]\n    \n    # Fetch enhanced data\n    enhanced_data = data_sources.fetch_enhanced_market_data(test_coins)\n    \n    # Generate analysis summary\n    analysis = data_sources.get_market_analysis_summary(enhanced_data)\n    \n    print(\"\\n📊 Market Analysis Summary:\")\n    print(f\"Market Sentiment: {analysis['market_sentiment']}\")\n    print(f\"Fear & Greed Score: {analysis['fear_greed_score']}\")\n    \n    if analysis['market_dominance']:\n        print(\"\\n💰 Market Dominance:\")\n        for symbol, data in analysis['market_dominance'].items():\n            print(f\"  {symbol}: {data}\")\n    \n    print(\"\\n✅ Enhanced data integration test complete!\")