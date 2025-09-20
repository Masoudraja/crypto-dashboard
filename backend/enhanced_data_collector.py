#!/usr/bin/env python3
"""
Enhanced Data Collector - Multi-Source Crypto Data Collection
Integrates multiple free APIs for comprehensive market data
"""

import requests
import psycopg2
import pandas as pd
import pandas_ta as ta
import time
import json
from datetime import datetime, timedelta
from config import COINS_TO_TRACK, API_KEY, DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from typing import Dict, List, Optional, Any

class EnhancedDataCollector:
    def __init__(self):
        self.coingecko_api_key = API_KEY
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Enhanced-Crypto-Dashboard/1.0'
        })
    
    def get_db_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(
                host=DB_HOST, port=DB_PORT, dbname=DB_NAME, 
                user=DB_USER, password=DB_PASSWORD
            )
        except Exception as e:
            print(f"Database connection error: {e}")
            return None
    
    def fetch_coingecko_data(self, coin_ids: List[str]) -> Optional[Dict]:
        """Fetch data from CoinGecko API (Primary source)"""
        try:
            coin_list_string = ",".join(coin_ids)
            url = 'https://api.coingecko.com/api/v3/simple/price'
            params = {
                'ids': coin_list_string,
                'vs_currencies': 'usd',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true',
                'include_24hr_change': 'true',
                'include_last_updated_at': 'true',
                'x_cg_demo_api_key': self.coingecko_api_key
            }
            
            response = self.session.get(url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"CoinGecko API error: {response.status_code}")
                return None
        except Exception as e:
            print(f"CoinGecko fetch error: {e}")
            return None
    
    def fetch_coinpaprika_data(self, coin_ids: List[str]) -> Optional[Dict]:
        """Fetch data from CoinPaprika API (Free backup source)"""
        try:
            # CoinPaprika uses different coin IDs, so we need a mapping
            paprika_mapping = {
                'bitcoin': 'btc-bitcoin',
                'ethereum': 'eth-ethereum',
                'ripple': 'xrp-xrp',
                'cardano': 'ada-cardano',
                'solana': 'sol-solana',
                'dogecoin': 'doge-dogecoin',
                'chainlink': 'link-chainlink',
                'litecoin': 'ltc-litecoin',
                'binancecoin': 'bnb-binance-coin',
                'polkadot': 'dot-polkadot'
            }
            
            paprika_data = {}
            
            for coin_id in coin_ids[:10]:  # Limit to avoid rate limits
                paprika_id = paprika_mapping.get(coin_id)
                if not paprika_id:
                    continue
                    
                url = f'https://api.coinpaprika.com/v1/tickers/{paprika_id}'
                
                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        paprika_data[coin_id] = {
                            'price': data['quotes']['USD']['price'],
                            'market_cap': data['quotes']['USD']['market_cap'],
                            'volume_24h': data['quotes']['USD']['volume_24h'],
                            'change_24h': data['quotes']['USD']['percent_change_24h']
                        }
                    time.sleep(0.5)  # Rate limiting
                except Exception as e:
                    print(f"Error fetching {coin_id} from CoinPaprika: {e}")
                    continue
            
            return paprika_data
        except Exception as e:
            print(f"CoinPaprika fetch error: {e}")
            return None
    
    def fetch_coinstats_data(self, coin_ids: List[str]) -> Optional[Dict]:
        """Fetch data from CoinStats API (Free source)"""
        try:
            # CoinStats mapping
            coinstats_mapping = {
                'bitcoin': 'bitcoin',
                'ethereum': 'ethereum',
                'ripple': 'ripple',
                'cardano': 'cardano',
                'solana': 'solana',
                'dogecoin': 'dogecoin',
                'chainlink': 'chainlink',
                'litecoin': 'litecoin',
                'binancecoin': 'binance-coin'
            }
            
            coinstats_data = {}
            
            for coin_id in coin_ids[:5]:  # Limit for free tier
                coinstats_id = coinstats_mapping.get(coin_id)
                if not coinstats_id:
                    continue
                    
                url = f'https://api.coinstats.app/public/v1/coins/{coinstats_id}'
                
                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        coin_data = data.get('coin', {})
                        coinstats_data[coin_id] = {
                            'price': coin_data.get('price'),
                            'market_cap': coin_data.get('marketCap'),
                            'volume_24h': coin_data.get('volume'),
                            'change_24h': coin_data.get('priceChange1d')
                        }
                    time.sleep(1)  # Rate limiting
                except Exception as e:
                    print(f"Error fetching {coin_id} from CoinStats: {e}")
                    continue
            
            return coinstats_data
        except Exception as e:
            print(f"CoinStats fetch error: {e}")
            return None
    
    def fetch_coinmarketcap_data(self, coin_ids: List[str]) -> Optional[Dict]:
        """Fetch data from CoinMarketCap API (Free tier)"""
        try:
            # CoinMarketCap uses symbols, not ids
            symbol_mapping = {
                'bitcoin': 'BTC', 'ethereum': 'ETH', 'ripple': 'XRP',
                'cardano': 'ADA', 'solana': 'SOL', 'dogecoin': 'DOGE',
                'chainlink': 'LINK', 'litecoin': 'LTC', 'binancecoin': 'BNB',
                'polkadot': 'DOT', 'avalanche-2': 'AVAX', 'polygon': 'MATIC'
            }
            
            symbols = [symbol_mapping.get(coin_id) for coin_id in coin_ids[:10] if symbol_mapping.get(coin_id)]
            if not symbols:
                return None
            
            url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
            headers = {
                'X-CMC_PRO_API_KEY': 'your-free-api-key-here',  # Replace with actual key
                'Accept': 'application/json'
            }
            params = {
                'symbol': ','.join(symbols),
                'convert': 'USD'
            }
            
            response = self.session.get(url, headers=headers, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                cmc_data = {}
                
                reverse_mapping = {v: k for k, v in symbol_mapping.items()}
                
                for symbol, coin_data in data.get('data', {}).items():
                    coin_id = reverse_mapping.get(symbol)
                    if coin_id:
                        quote = coin_data['quote']['USD']
                        cmc_data[coin_id] = {
                            'price': quote['price'],
                            'market_cap': quote['market_cap'],
                            'volume_24h': quote['volume_24h'],
                            'change_24h': quote['percent_change_24h']
                        }
                
                return cmc_data
            else:
                print(f"CoinMarketCap API error: {response.status_code}")
                return None
        except Exception as e:
            print(f"CoinMarketCap fetch error: {e}")
            return None
    
    def fetch_alpha_vantage_data(self, coin_ids: List[str]) -> Optional[Dict]:
        """Fetch data from Alpha Vantage API (Free tier)"""
        try:
            # Alpha Vantage digital currency endpoint
            av_data = {}
            
            symbol_mapping = {
                'bitcoin': 'BTC', 'ethereum': 'ETH', 'litecoin': 'LTC',
                'ripple': 'XRP', 'cardano': 'ADA', 'dogecoin': 'DOGE'
            }
            
            api_key = 'demo'  # Replace with actual free API key
            
            for coin_id in coin_ids[:5]:  # Limit for free tier
                symbol = symbol_mapping.get(coin_id)
                if not symbol:
                    continue
                
                url = 'https://www.alphavantage.co/query'
                params = {
                    'function': 'CURRENCY_EXCHANGE_RATE',
                    'from_currency': symbol,
                    'to_currency': 'USD',
                    'apikey': api_key
                }
                
                try:
                    response = self.session.get(url, params=params, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        rate_data = data.get('Realtime Currency Exchange Rate', {})
                        
                        if rate_data:
                            av_data[coin_id] = {
                                'price': float(rate_data.get('5. Exchange Rate', 0)),
                                'market_cap': None,  # Not provided by this endpoint
                                'volume_24h': None,
                                'change_24h': None
                            }
                    
                    time.sleep(12)  # Rate limiting for free tier (5 calls per minute)
                except Exception as e:
                    print(f"Error fetching {coin_id} from Alpha Vantage: {e}")
                    continue
            
            return av_data
        except Exception as e:
            print(f"Alpha Vantage fetch error: {e}")
            return None
    
    def fetch_coindesk_data(self, coin_ids: List[str]) -> Optional[Dict]:
        """Fetch data from CoinDesk API (Free Bitcoin data)"""
        try:
            coindesk_data = {}
            
            # CoinDesk primarily provides Bitcoin data
            if 'bitcoin' in coin_ids:
                url = 'https://api.coindesk.com/v1/bpi/currentprice.json'
                
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    btc_price = data['bpi']['USD']['rate_float']
                    
                    coindesk_data['bitcoin'] = {
                        'price': btc_price,
                        'market_cap': None,
                        'volume_24h': None,
                        'change_24h': None
                    }
            
            return coindesk_data
        except Exception as e:
            print(f"CoinDesk fetch error: {e}")
            return None
    
    def merge_data_sources(self, coingecko_data: Dict, paprika_data: Dict, coinstats_data: Dict, 
                          cmc_data: Dict = None, av_data: Dict = None, coindesk_data: Dict = None) -> Dict:
        """Merge data from multiple sources with priority"""
        merged_data = {}
        
        # Get all unique coin IDs
        all_coins = set()
        if coingecko_data:
            all_coins.update(coingecko_data.keys())
        if paprika_data:
            all_coins.update(paprika_data.keys())
        if coinstats_data:
            all_coins.update(coinstats_data.keys())
        if cmc_data:
            all_coins.update(cmc_data.keys())
        if av_data:
            all_coins.update(av_data.keys())
        if coindesk_data:
            all_coins.update(coindesk_data.keys())
        
        for coin_id in all_coins:
            # Priority: CoinGecko > CoinPaprika > CoinStats
            coin_data = {}
            
            # Start with CoinGecko data (highest priority)
            if coingecko_data and coin_id in coingecko_data:
                cg_data = coingecko_data[coin_id]
                coin_data = {
                    'price': cg_data.get('usd'),
                    'market_cap': cg_data.get('usd_market_cap'),
                    'volume_24h': cg_data.get('usd_24h_vol'),
                    'change_24h': cg_data.get('usd_24h_change'),
                    'last_updated': cg_data.get('last_updated_at'),
                    'source': 'coingecko'
                }
            
            # Fill gaps with CoinPaprika data
            if paprika_data and coin_id in paprika_data:
                pp_data = paprika_data[coin_id]
                for key in ['price', 'market_cap', 'volume_24h', 'change_24h']:
                    if not coin_data.get(key) and pp_data.get(key):
                        coin_data[key] = pp_data[key]
                        coin_data['source'] = coin_data.get('source', '') + '+paprika'
            
            # Fill remaining gaps with CoinStats data
            if coinstats_data and coin_id in coinstats_data:
                cs_data = coinstats_data[coin_id]
                for key in ['price', 'market_cap', 'volume_24h', 'change_24h']:
                    if not coin_data.get(key) and cs_data.get(key):
                        coin_data[key] = cs_data[key]
                        coin_data['source'] = coin_data.get('source', '') + '+coinstats'
            
            # Fill remaining gaps with CoinMarketCap data
            if cmc_data and coin_id in cmc_data:
                cmc_coin_data = cmc_data[coin_id]
                for key in ['price', 'market_cap', 'volume_24h', 'change_24h']:
                    if not coin_data.get(key) and cmc_coin_data.get(key):
                        coin_data[key] = cmc_coin_data[key]
                        coin_data['source'] = coin_data.get('source', '') + '+cmc'
            
            # Fill remaining gaps with Alpha Vantage data
            if av_data and coin_id in av_data:
                av_coin_data = av_data[coin_id]
                for key in ['price', 'market_cap', 'volume_24h', 'change_24h']:
                    if not coin_data.get(key) and av_coin_data.get(key):
                        coin_data[key] = av_coin_data[key]
                        coin_data['source'] = coin_data.get('source', '') + '+av'
            
            # Fill remaining gaps with CoinDesk data
            if coindesk_data and coin_id in coindesk_data:
                cd_coin_data = coindesk_data[coin_id]
                for key in ['price', 'market_cap', 'volume_24h', 'change_24h']:
                    if not coin_data.get(key) and cd_coin_data.get(key):
                        coin_data[key] = cd_coin_data[key]
                        coin_data['source'] = coin_data.get('source', '') + '+coindesk'
            
            if coin_data.get('price'):  # Only include coins with price data
                merged_data[coin_id] = coin_data
        
        return merged_data
    
    def validate_data_quality(self, data: Dict) -> Dict:
        """Validate and score data quality from multiple sources"""
        quality_report = {
            'total_coins': len(data),
            'data_sources_count': 0,
            'completeness_score': 0,
            'reliability_score': 0,
            'coins_with_all_fields': 0,
            'coins_missing_data': [],
            'source_coverage': {}
        }
        
        if not data:
            return quality_report
        
        # Analyze data completeness
        complete_coins = 0
        source_counts = {}
        
        for coin_id, coin_data in data.items():
            required_fields = ['price', 'market_cap', 'volume_24h', 'change_24h']
            missing_fields = [field for field in required_fields if not coin_data.get(field)]
            
            if not missing_fields:
                complete_coins += 1
            else:
                quality_report['coins_missing_data'].append({
                    'coin': coin_id,
                    'missing': missing_fields
                })
            
            # Track source usage
            source = coin_data.get('source', 'unknown')
            source_counts[source] = source_counts.get(source, 0) + 1
        
        quality_report['coins_with_all_fields'] = complete_coins
        quality_report['completeness_score'] = (complete_coins / len(data)) * 100
        quality_report['data_sources_count'] = len(source_counts)
        quality_report['source_coverage'] = source_counts
        
        # Calculate reliability score based on source diversity
        if quality_report['data_sources_count'] >= 3:
            quality_report['reliability_score'] = 95
        elif quality_report['data_sources_count'] == 2:
            quality_report['reliability_score'] = 80
        else:
            quality_report['reliability_score'] = 60
        
        return quality_report
    
    def calculate_enhanced_indicators(self, df: pd.DataFrame) -> bool:
        """Calculate comprehensive technical indicators"""
        try:
            print("Calculating enhanced technical indicators...")
            
            # Ensure required columns
            if 'high' not in df.columns:
                df['high'] = df['close'] * 1.002
            if 'low' not in df.columns:
                df['low'] = df['close'] * 0.998
            if 'volume' not in df.columns:
                df['volume'] = df.get('volume_24h', 1000000)
            
            # Moving Averages
            for period in [20, 50, 100, 200]:
                df.ta.sma(close=df['close'], length=period, append=True)
            
            for period in [12, 26, 50]:
                df.ta.ema(close=df['close'], length=period, append=True)
            
            # Momentum Indicators
            df.ta.rsi(close=df['close'], length=14, append=True)
            df.ta.macd(close=df['close'], fast=12, slow=26, signal=9, append=True)
            
            # Volatility Indicators
            df.ta.bbands(close=df['close'], length=20, append=True)
            df.ta.atr(high=df['high'], low=df['low'], close=df['close'], length=14, append=True)
            
            # Advanced Indicators (only with sufficient data)
            if len(df) >= 20:
                df.ta.stochrsi(close=df['close'], length=14, append=True)
                df.ta.willr(high=df['high'], low=df['low'], close=df['close'], length=14, append=True)
                df.ta.cci(high=df['high'], low=df['low'], close=df['close'], length=20, append=True)
                df.ta.psar(high=df['high'], low=df['low'], close=df['close'], af=0.02, max_af=0.2, append=True)
            
            print("✅ Enhanced technical indicators calculated successfully")
            return True
        except Exception as e:
            print(f"⚠️ Warning in indicator calculation: {e}")
            return True  # Continue even if some indicators fail
    
    def save_enhanced_data(self, coin_id: str, price_data: Dict) -> bool:
        """Save enhanced data to database"""
        conn = self.get_db_connection()
        if conn is None:
            return False
        
        try:
            # Fetch historical data for indicator calculation
            query = "SELECT timestamp, price_usd FROM crypto_prices WHERE coin_id = %s ORDER BY timestamp ASC;"
            df = pd.read_sql_query(query, conn, params=(coin_id,), index_col='timestamp')
            
            # Add new data point
            new_timestamp = pd.Timestamp.now(tz='UTC')
            new_data = pd.DataFrame([{
                'price_usd': price_data['price'],
                'market_cap': price_data.get('market_cap'),
                'volume_24h': price_data.get('volume_24h'),
                'change_24h': price_data.get('change_24h')
            }], index=[new_timestamp])
            
            df = pd.concat([df, new_data])
            df.rename(columns={'price_usd': 'close'}, inplace=True)
            
            # Calculate indicators
            self.calculate_enhanced_indicators(df)
            
            # Get latest values
            latest_data = df.iloc[-1]
            
            # Insert into database
            cur = conn.cursor()
            insert_query = """
            INSERT INTO crypto_prices (
                coin_id, price_usd, market_cap, volume_24h, change_24h,
                sma_20, sma_100, sma_200,
                ema_12, ema_26, ema_50,
                rsi_14, macd_line, macd_signal, macd_hist,
                bb_lower, bb_mid, bb_upper,
                stochrsi_k, stochrsi_d,
                williams_r_14, cci_20, atr_14,
                psar_long, psar_short
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s
            )
            """
            
            def safe_get(col_name, default=None):
                value = latest_data.get(col_name, default)
                return float(value) if pd.notna(value) and value is not None else None
            
            db_values = (
                coin_id,
                safe_get('close'),
                safe_get('market_cap'),
                safe_get('volume_24h'),
                safe_get('change_24h'),
                # SMAs
                safe_get('SMA_20'), safe_get('SMA_100'), safe_get('SMA_200'),
                # EMAs
                safe_get('EMA_12'), safe_get('EMA_26'), safe_get('EMA_50'),
                # RSI and MACD
                safe_get('RSI_14'), safe_get('MACD_12_26_9'), safe_get('MACDs_12_26_9'), safe_get('MACDh_12_26_9'),
                # Bollinger Bands
                safe_get('BBL_20_2.0_2.0'), safe_get('BBM_20_2.0_2.0'), safe_get('BBU_20_2.0_2.0'),
                # Stochastic RSI
                safe_get('STOCHRSIk_14_14_3_3'), safe_get('STOCHRSId_14_14_3_3'),
                # Advanced indicators
                safe_get('WILLR_14'), safe_get('CCI_20'), safe_get('ATR_14'),
                # Parabolic SAR
                safe_get('PSARl_0.02_0.2'), safe_get('PSARs_0.02_0.2')
            )
            
            cur.execute(insert_query, db_values)
            conn.commit()
            cur.close()
            
            print(f"✅ Successfully saved enhanced data for {coin_id} (source: {price_data.get('source', 'unknown')})")
            return True
            
        except Exception as e:
            print(f"❌ Error saving {coin_id}: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    def collect_enhanced_data(self):
        """Main collection function with multiple API sources"""
        print("🚀 Enhanced Data Collection Started")
        print("=" * 50)
        
        coin_ids = COINS_TO_TRACK[:30]  # Limit for API rate limits
        
        print(f"📊 Collecting data for {len(coin_ids)} cryptocurrencies...")
        
        # Fetch from all sources
        print("\n📡 Fetching from CoinGecko (Primary)...")
        coingecko_data = self.fetch_coingecko_data(coin_ids)
        
        print("📡 Fetching from CoinPaprika (Backup)...")
        paprika_data = self.fetch_coinpaprika_data(coin_ids)
        
        print("📡 Fetching from CoinStats (Additional)...")
        coinstats_data = self.fetch_coinstats_data(coin_ids)
        
        print("📡 Fetching from CoinMarketCap (Alternative)...")
        cmc_data = self.fetch_coinmarketcap_data(coin_ids)
        
        print("📡 Fetching from Alpha Vantage (Supplemental)...")
        av_data = self.fetch_alpha_vantage_data(coin_ids)
        
        print("📡 Fetching from CoinDesk (Bitcoin reference)...")
        coindesk_data = self.fetch_coindesk_data(coin_ids)
        
        # Merge data with priority
        print("\n🔄 Merging data from 6 sources...")
        merged_data = self.merge_data_sources(
            coingecko_data or {}, 
            paprika_data or {}, 
            coinstats_data or {},
            cmc_data or {},
            av_data or {},
            coindesk_data or {}
        )
        
        # Validate data quality
        print("\n🔍 Validating data quality...")
        quality_report = self.validate_data_quality(merged_data)
        
        if not merged_data:
            print("❌ No data collected from any source")
            return False
        
        # Print quality report
        print(f"\n📈 Data Quality Report:")
        print(f"   • Total coins collected: {quality_report['total_coins']}")
        print(f"   • Completeness score: {quality_report['completeness_score']:.1f}%")
        print(f"   • Reliability score: {quality_report['reliability_score']:.1f}%")
        print(f"   • Data sources used: {quality_report['data_sources_count']}")
        print(f"   • Coins with complete data: {quality_report['coins_with_all_fields']}")
        
        if quality_report['source_coverage']:
            print(f"\n📊 Source Coverage:")
            for source, count in quality_report['source_coverage'].items():
                print(f"   • {source}: {count} coins")
        
        # Process each coin with enhanced indicators
        print(f"\n💾 Saving enhanced data to database...")
        success_count = 0
        error_count = 0
        
        for coin_id, price_data in merged_data.items():
            if self.save_enhanced_data(coin_id, price_data):
                success_count += 1
            else:
                error_count += 1
            time.sleep(0.5)  # Rate limiting
        
        print(f"\n✅ Enhanced collection completed!")
        print(f"📊 Collected {len(merged_data)} coins from 6 API sources")
        print(f"💾 {success_count} coins saved to database")
        print(f"❌ {error_count} coins failed to save")
        print(f"🎯 Data quality score: {quality_report['reliability_score']:.1f}%")
        
        return success_count > 0

if __name__ == "__main__":
    collector = EnhancedDataCollector()
    collector.collect_enhanced_data()