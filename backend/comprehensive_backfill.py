#!/usr/bin/env python3
"""
Comprehensive Data Backfill Script
Ensures sufficient historical data for proper indicator calculations
"""

import requests
import psycopg2
import pandas as pd
import pandas_ta as ta
import time
import json
from datetime import datetime, timedelta
from config import COINS_TO_TRACK, API_KEY, DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from typing import Dict, List, Optional

class ComprehensiveBackfillEngine:
    def __init__(self):
        self.api_key = API_KEY
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Crypto-Dashboard-Backfill/1.0'
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
    
    def check_data_coverage(self) -> Dict[str, int]:
        """Check how much data we have for each coin"""
        conn = self.get_db_connection()
        if conn is None:
            return {}
        
        try:
            cur = conn.cursor()
            query = """
                SELECT coin_id, COUNT(*) as records, 
                       MIN(timestamp) as earliest, 
                       MAX(timestamp) as latest,
                       COUNT(*) FILTER (WHERE sma_20 IS NOT NULL) as indicators_count
                FROM crypto_prices 
                GROUP BY coin_id
                ORDER BY records DESC;
            """
            
            cur.execute(query)
            results = cur.fetchall()
            
            coverage = {}
            print(f"📊 Current Data Coverage:")
            print("-" * 60)
            
            for coin_id, records, earliest, latest, indicators in results:
                days_coverage = (latest - earliest).days if earliest and latest else 0
                coverage[coin_id] = {
                    'records': records,
                    'days_coverage': days_coverage,
                    'indicators_count': indicators,
                    'earliest': earliest,
                    'latest': latest
                }
                
                print(f"{coin_id:<20} | {records:>6} records | {days_coverage:>3} days | {indicators:>4} indicators")
            
            cur.close()
            conn.close()
            return coverage
            
        except Exception as e:
            print(f"Error checking coverage: {e}")
            return {}
    
    def fetch_historical_data(self, coin_id: str, days: int = 90) -> Optional[List[Dict]]:
        """Fetch historical data from CoinGecko"""
        try:
            print(f"📡 Fetching {days} days of data for {coin_id}...")
            
            url = f'https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart'
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'hourly' if days <= 90 else 'daily',
                'x_cg_demo_api_key': self.api_key
            }
            
            response = self.session.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                
                # Process the data into records
                prices = data.get('prices', [])
                market_caps = data.get('market_caps', [])
                volumes = data.get('total_volumes', [])
                
                records = []
                for i, (timestamp, price) in enumerate(prices):
                    # Convert timestamp from milliseconds
                    dt = datetime.fromtimestamp(timestamp / 1000)
                    
                    record = {
                        'timestamp': dt,
                        'price_usd': price,
                        'market_cap': market_caps[i][1] if i < len(market_caps) else None,
                        'volume_24h': volumes[i][1] if i < len(volumes) else None,
                        'change_24h': None  # Will be calculated
                    }
                    records.append(record)
                
                # Calculate 24h changes
                for i in range(1, len(records)):
                    prev_price = records[i-1]['price_usd']
                    curr_price = records[i]['price_usd']
                    if prev_price and curr_price:
                        change = ((curr_price - prev_price) / prev_price) * 100
                        records[i]['change_24h'] = change
                
                print(f"✅ Retrieved {len(records)} historical records for {coin_id}")
                return records
                
            else:
                print(f"❌ API error for {coin_id}: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error fetching historical data for {coin_id}: {e}")
            return None
    
    def calculate_comprehensive_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all indicators for historical data"""
        try:
            print("🧮 Calculating comprehensive indicators...")
            
            # Ensure we have the required columns
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
                
                if len(df) >= 50:
                    df.ta.psar(high=df['high'], low=df['low'], close=df['close'], af=0.02, max_af=0.2, append=True)
            
            print(f"✅ Calculated indicators for {len(df)} records")
            return df
            
        except Exception as e:
            print(f"⚠️ Error in indicator calculation: {e}")
            return df
    
    def save_historical_data(self, coin_id: str, records: List[Dict]) -> int:
        """Save historical data with indicators to database"""
        conn = self.get_db_connection()
        if conn is None:
            return 0
        
        try:
            # Convert to DataFrame for indicator calculation
            df = pd.DataFrame(records)
            df.set_index('timestamp', inplace=True)
            df.rename(columns={'price_usd': 'close'}, inplace=True)
            
            # Calculate indicators
            df = self.calculate_comprehensive_indicators(df)
            
            # Save to database
            cur = conn.cursor()
            saved_count = 0
            
            for timestamp, row in df.iterrows():
                try:
                    # Helper function to safely get float values
                    def safe_float(value, default=None):
                        if pd.isna(value) or value is None:
                            return default
                        return float(value)
                    
                    # Insert query
                    insert_query = """
                    INSERT INTO crypto_prices (
                        coin_id, timestamp, price_usd, market_cap, volume_24h, change_24h,
                        sma_20, sma_50, sma_100, sma_200,
                        ema_12, ema_26, ema_50,
                        rsi_14, macd_line, macd_signal, macd_hist,
                        bb_lower, bb_mid, bb_upper,
                        stochrsi_k, stochrsi_d,
                        williams_r_14, cci_20, atr_14,
                        psar_long, psar_short
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s,
                        %s, %s, %s,
                        %s, %s
                    )
                    ON CONFLICT (coin_id, timestamp) DO UPDATE SET
                        sma_20 = EXCLUDED.sma_20,
                        sma_50 = EXCLUDED.sma_50,
                        sma_100 = EXCLUDED.sma_100,
                        sma_200 = EXCLUDED.sma_200,
                        ema_12 = EXCLUDED.ema_12,
                        ema_26 = EXCLUDED.ema_26,
                        ema_50 = EXCLUDED.ema_50,
                        rsi_14 = EXCLUDED.rsi_14,
                        macd_line = EXCLUDED.macd_line,
                        macd_signal = EXCLUDED.macd_signal,
                        macd_hist = EXCLUDED.macd_hist,
                        bb_lower = EXCLUDED.bb_lower,
                        bb_mid = EXCLUDED.bb_mid,
                        bb_upper = EXCLUDED.bb_upper,
                        stochrsi_k = EXCLUDED.stochrsi_k,
                        stochrsi_d = EXCLUDED.stochrsi_d,
                        williams_r_14 = EXCLUDED.williams_r_14,
                        cci_20 = EXCLUDED.cci_20,
                        atr_14 = EXCLUDED.atr_14,
                        psar_long = EXCLUDED.psar_long,
                        psar_short = EXCLUDED.psar_short;
                    """
                    
                    values = (
                        coin_id,
                        timestamp,
                        safe_float(row.get('close')),
                        safe_float(row.get('market_cap')),
                        safe_float(row.get('volume_24h')),
                        safe_float(row.get('change_24h')),
                        # SMAs
                        safe_float(row.get('SMA_20')),
                        safe_float(row.get('SMA_50')),
                        safe_float(row.get('SMA_100')),
                        safe_float(row.get('SMA_200')),
                        # EMAs
                        safe_float(row.get('EMA_12')),
                        safe_float(row.get('EMA_26')),
                        safe_float(row.get('EMA_50')),
                        # RSI and MACD
                        safe_float(row.get('RSI_14')),
                        safe_float(row.get('MACD_12_26_9')),
                        safe_float(row.get('MACDs_12_26_9')),
                        safe_float(row.get('MACDh_12_26_9')),
                        # Bollinger Bands
                        safe_float(row.get('BBL_20_2.0')),
                        safe_float(row.get('BBM_20_2.0')),
                        safe_float(row.get('BBU_20_2.0')),
                        # Stochastic RSI
                        safe_float(row.get('STOCHRSIk_14_14_3_3')),
                        safe_float(row.get('STOCHRSId_14_14_3_3')),
                        # Advanced indicators
                        safe_float(row.get('WILLR_14')),
                        safe_float(row.get('CCI_20')),
                        safe_float(row.get('ATR_14')),
                        # Parabolic SAR
                        safe_float(row.get('PSARl_0.02_0.2')),
                        safe_float(row.get('PSARs_0.02_0.2'))
                    )
                    
                    cur.execute(insert_query, values)
                    saved_count += 1
                    
                except Exception as row_error:
                    print(f"⚠️ Error saving row for {coin_id} at {timestamp}: {row_error}")
                    continue
            
            conn.commit()
            cur.close()
            conn.close()
            
            print(f"✅ Saved {saved_count} records with indicators for {coin_id}")
            return saved_count
            
        except Exception as e:
            print(f"❌ Error saving historical data for {coin_id}: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return 0
    
    def run_comprehensive_backfill(self, days: int = 90, force_update: bool = False):
        """Run comprehensive backfill for all coins"""
        print("🚀 Starting Comprehensive Data Backfill")
        print("=" * 60)
        print(f"Target: {days} days of historical data with full indicators")
        print(f"Coins: {len(COINS_TO_TRACK[:20])} cryptocurrencies")  # Limit for API constraints
        print()
        
        # Check current coverage
        coverage = self.check_data_coverage()
        print()
        
        # Process each coin
        total_saved = 0
        coins_processed = 0
        
        for coin_id in COINS_TO_TRACK[:20]:  # Process first 20 coins
            try:
                print(f"\n🔄 Processing {coin_id}...")
                
                # Check if we need to backfill this coin
                current_coverage = coverage.get(coin_id, {})
                current_days = current_coverage.get('days_coverage', 0)
                indicators_count = current_coverage.get('indicators_count', 0)
                
                if not force_update and current_days >= days and indicators_count > 100:
                    print(f"✅ {coin_id} already has sufficient data ({current_days} days, {indicators_count} indicators)")
                    continue
                
                # Fetch historical data
                records = self.fetch_historical_data(coin_id, days)
                if not records:
                    print(f"❌ Failed to fetch data for {coin_id}")
                    continue
                
                # Save with indicators
                saved_count = self.save_historical_data(coin_id, records)
                total_saved += saved_count
                coins_processed += 1
                
                print(f"✅ {coin_id}: {saved_count} records saved")
                
                # Rate limiting
                time.sleep(2)  # Be respectful to the API
                
            except Exception as e:
                print(f"❌ Error processing {coin_id}: {e}")
                continue
        
        # Final summary
        print("\n" + "=" * 60)
        print("📊 BACKFILL COMPLETE")
        print("=" * 60)
        print(f"✅ Coins processed: {coins_processed}")
        print(f"✅ Total records saved: {total_saved}")
        print(f"✅ Average records per coin: {total_saved // max(coins_processed, 1)}")
        
        # Check final coverage
        print(f"\n📈 Final Data Coverage:")
        final_coverage = self.check_data_coverage()
        
        return coins_processed > 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive Data Backfill")
    parser.add_argument("--days", type=int, default=90, help="Days of historical data to fetch")
    parser.add_argument("--force", action="store_true", help="Force update even if data exists")
    
    args = parser.parse_args()
    
    engine = ComprehensiveBackfillEngine()
    success = engine.run_comprehensive_backfill(days=args.days, force_update=args.force)
    
    if success:
        print("\n🎉 Backfill completed successfully!")
        print("💡 Your indicators should now work properly with sufficient historical data.")
    else:
        print("\n❌ Backfill failed or no data was processed.")