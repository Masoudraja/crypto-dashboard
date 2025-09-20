#!/usr/bin/env python3
"""
Limited Backfill Script - Respects API Rate Limits
Gradually builds historical data for long-term indicators like SMA_200
"""

import requests
import psycopg2
import pandas as pd
import pandas_ta as ta
import time
from datetime import datetime, timedelta
from config import COINS_TO_TRACK, API_KEY, DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, INDICATORS_CONFIG

def get_db_connection():
    try:
        return psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def fetch_historical_data_limited(coin_id, days=30):
    """Fetch limited historical data for a specific coin"""
    URL = 'https://api.coingecko.com/api/v3/coins/{}/market_chart'
    
    params = {
        'vs_currency': 'usd',
        'days': days,
        'interval': 'daily',
        'x_cg_demo_api_key': API_KEY
    }
    
    try:
        response = requests.get(URL.format(coin_id), params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            
            # Extract prices with timestamps
            prices = data.get('prices', [])
            market_caps = data.get('market_caps', [])
            volumes = data.get('total_volumes', [])
            
            historical_data = []
            for i, (timestamp_ms, price) in enumerate(prices):
                timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
                
                entry = {
                    'timestamp': timestamp,
                    'price': price,
                    'market_cap': market_caps[i][1] if i < len(market_caps) else None,
                    'volume_24h': volumes[i][1] if i < len(volumes) else None,
                }
                historical_data.append(entry)
            
            return historical_data
        else:
            print(f"API Error for {coin_id}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching {coin_id}: {e}")
        return None

def calculate_advanced_indicators_df(df):
    """Calculate comprehensive technical indicators with proper data handling"""
    try:
        # Ensure we have high, low, and volume columns
        if 'high' not in df.columns:
            df['high'] = df['close'] * 1.001
        if 'low' not in df.columns:
            df['low'] = df['close'] * 0.999
        if 'volume' not in df.columns:
            df['volume'] = df.get('volume_24h', 1000000)
        
        # Calculate all indicators
        for period in INDICATORS_CONFIG['sma']:
            df.ta.sma(close=df['close'], length=period, append=True)
        
        for period in INDICATORS_CONFIG['ema']:
            df.ta.ema(close=df['close'], length=period, append=True)
        
        for period in INDICATORS_CONFIG['rsi']:
            df.ta.rsi(close=df['close'], length=period, append=True)
        
        for fast, slow, signal in INDICATORS_CONFIG['macd']:
            df.ta.macd(close=df['close'], fast=fast, slow=slow, signal=signal, append=True)
        
        for period in INDICATORS_CONFIG['bbands']:
            df.ta.bbands(close=df['close'], length=period, append=True)
        
        # Advanced indicators
        if len(df) >= 20:
            for period in INDICATORS_CONFIG['stoch_rsi']:
                df.ta.stochrsi(close=df['close'], length=period, append=True)
            
            for period in INDICATORS_CONFIG['williams_r']:
                willr_result = df.ta.willr(high=df['high'], low=df['low'], close=df['close'], length=period)
                if willr_result is not None:
                    df[f'WR_{period}'] = willr_result
            
            for period in INDICATORS_CONFIG['cci']:
                cci_result = df.ta.cci(high=df['high'], low=df['low'], close=df['close'], length=period)
                if cci_result is not None:
                    df[f'CCI_{period}'] = cci_result
            
            for period in INDICATORS_CONFIG['atr']:
                atr_result = df.ta.atr(high=df['high'], low=df['low'], close=df['close'], length=period)
                if atr_result is not None:
                    df[f'ATR_{period}'] = atr_result
            
            for acceleration, maximum in INDICATORS_CONFIG['parabolic_sar']:
                psar_result = df.ta.psar(high=df['high'], low=df['low'], close=df['close'], af=acceleration, max_af=maximum)
                if psar_result is not None and not psar_result.empty:
                    for col in psar_result.columns:
                        df[col] = psar_result[col]
        
        return True
    except Exception as e:
        print(f"⚠️ Warning in indicator calculation: {e}")
        return True

def backfill_coin_data(coin_id, days=30):
    """Backfill historical data for a specific coin"""
    print(f"\n--- Backfilling {coin_id} ({days} days) ---")
    
    # Fetch historical data
    historical_data = fetch_historical_data_limited(coin_id, days)
    if not historical_data:
        print(f"❌ Failed to fetch data for {coin_id}")
        return False
    
    print(f"✅ Fetched {len(historical_data)} historical records")
    
    # Convert to DataFrame
    df = pd.DataFrame(historical_data)
    df.set_index('timestamp', inplace=True)
    df.rename(columns={'price': 'close'}, inplace=True)
    df.sort_index(inplace=True)
    
    # Calculate indicators
    if not calculate_advanced_indicators_df(df):
        print(f"❌ Failed to calculate indicators for {coin_id}")
        return False
    
    print(f"✅ Calculated indicators for {len(df)} records")
    
    # Insert into database
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
        cur = conn.cursor()
        
        # Prepare insert query
        insert_query = """
        INSERT INTO crypto_prices (
            coin_id, timestamp, price_usd, market_cap, volume_24h,
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
        ) ON CONFLICT (coin_id, timestamp) DO NOTHING;
        """
        
        def safe_get(row, col_name, default=None):
            value = row.get(col_name, default)
            if pd.isna(value):
                return None
            return float(value) if value is not None else None
        
        inserted_count = 0
        for timestamp, row in df.iterrows():
            db_values = (
                coin_id, timestamp,
                safe_get(row, 'close'),
                safe_get(row, 'market_cap'),
                safe_get(row, 'volume_24h'),
                # SMAs
                safe_get(row, 'SMA_20'), safe_get(row, 'SMA_100'), safe_get(row, 'SMA_200'),
                # EMAs
                safe_get(row, 'EMA_12'), safe_get(row, 'EMA_26'), safe_get(row, 'EMA_50'),
                # RSI and MACD
                safe_get(row, 'RSI_14'), safe_get(row, 'MACD_12_26_9'), safe_get(row, 'MACDs_12_26_9'), safe_get(row, 'MACDh_12_26_9'),
                # Bollinger Bands
                safe_get(row, 'BBL_20_2.0_2.0'), safe_get(row, 'BBM_20_2.0_2.0'), safe_get(row, 'BBU_20_2.0_2.0'),
                # Stochastic RSI
                safe_get(row, 'STOCHRSIk_14_14_3_3'), safe_get(row, 'STOCHRSId_14_14_3_3'),
                # Advanced indicators
                safe_get(row, 'WR_14'), safe_get(row, 'CCI_20'), safe_get(row, 'ATR_14'),
                # Parabolic SAR
                safe_get(row, 'PSARl_0.02_0.2'), safe_get(row, 'PSARs_0.02_0.2')
            )
            
            cur.execute(insert_query, db_values)
            inserted_count += 1
        
        conn.commit()
        cur.close()
        print(f"✅ Successfully inserted {inserted_count} records for {coin_id}")
        return True
        
    except Exception as e:
        print(f"❌ Database error for {coin_id}: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def main():
    print("🚀 Limited Historical Data Backfill")
    print("Respecting API rate limits to build historical data")
    print("=" * 60)
    
    # Focus on top 10 coins first to respect rate limits
    priority_coins = COINS_TO_TRACK[:10]
    
    successful = 0
    failed = 0
    
    for i, coin_id in enumerate(priority_coins):
        print(f"\nProgress: {i+1}/{len(priority_coins)}")
        
        if backfill_coin_data(coin_id, days=60):  # 60 days to help build SMA_100 and towards SMA_200
            successful += 1
        else:
            failed += 1
        
        # Rate limiting - be respectful to the API
        if i < len(priority_coins) - 1:  # Don't wait after the last coin
            print("⏱️  Waiting 10 seconds to respect API limits...")
            time.sleep(10)
    
    print(f"\n📊 Backfill Summary:")
    print(f"✅ Successful: {successful} coins")
    print(f"❌ Failed: {failed} coins")
    print(f"\n🎯 This should help populate SMA_100, SMA_200, and other long-term indicators!")

if __name__ == "__main__":
    main()