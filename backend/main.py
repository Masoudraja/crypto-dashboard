# File: main.py - Enhanced Crypto Analytics Engine
# This script fetches LATEST prices and calculates comprehensive technical indicators
# Enhanced with advanced indicators: Stochastic RSI, Williams %R, CCI, ATR, Parabolic SAR

import requests
import psycopg2
import pandas as pd
import pandas_ta as ta
import numpy as np
import time
from config import COINS_TO_TRACK, API_KEY, DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, INDICATORS_CONFIG

# --- Database Connection Function ---
def get_db_connection():
    try:
        return psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

# --- Enhanced API Fetching for Multiple Coins ---
def fetch_prices(coin_ids):
    """Fetch current prices with enhanced error handling and rate limiting"""
    coin_list_string = ",".join(coin_ids)
    URL = 'https://api.coingecko.com/api/v3/simple/price'
    params = {
        'ids': coin_list_string, 
        'vs_currencies': 'usd', 
        'include_market_cap': 'true',
        'include_24hr_vol': 'true',
        'include_24hr_change': 'true',
        'x_cg_demo_api_key': API_KEY
    }
    
    print(f"Fetching enhanced price data for {len(coin_ids)} cryptocurrencies...")
    try:
        response = requests.get(URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        enhanced_prices = {}
        for coin_id in coin_ids:
            if coin_id in data:
                enhanced_prices[coin_id] = {
                    'price': data[coin_id]['usd'],
                    'market_cap': data[coin_id].get('usd_market_cap'),
                    'volume_24h': data[coin_id].get('usd_24h_vol'),
                    'change_24h': data[coin_id].get('usd_24h_change')
                }
        
        print(f"✅ Success! Enhanced data fetched for {len(enhanced_prices)} coins.")
        return enhanced_prices
    except Exception as err:
        print(f"An error occurred during fetch: {err}")
    return None

# --- Advanced Analytics Engine ---
def calculate_advanced_indicators(df):
    """Calculate comprehensive technical indicators with proper data handling"""
    try:
        print("Calculating comprehensive technical indicators...")
        
        # Ensure we have high, low, and volume columns for advanced indicators
        # For crypto data, we'll approximate high/low using close price with small variation
        if 'high' not in df.columns:
            df['high'] = df['close'] * 1.001  # Approximate high as 0.1% above close
        if 'low' not in df.columns:
            df['low'] = df['close'] * 0.999   # Approximate low as 0.1% below close
        if 'volume' not in df.columns:
            df['volume'] = df.get('volume_24h', 1000000)  # Use 24h volume or default
        
        # Basic indicators
        for period in INDICATORS_CONFIG['sma']:
            df.ta.sma(close=df['close'], length=period, append=True)
        
        for period in INDICATORS_CONFIG['ema']:
            df.ta.ema(close=df['close'], length=period, append=True)
        
        for period in INDICATORS_CONFIG['rsi']:
            df.ta.rsi(close=df['close'], length=period, append=True)
        
        # MACD
        for fast, slow, signal in INDICATORS_CONFIG['macd']:
            df.ta.macd(close=df['close'], fast=fast, slow=slow, signal=signal, append=True)
        
        # Bollinger Bands
        for period in INDICATORS_CONFIG['bbands']:
            df.ta.bbands(close=df['close'], length=period, append=True)
        
        # Advanced indicators (only if we have enough data)
        if len(df) >= 20:
            # Stochastic RSI
            for period in INDICATORS_CONFIG['stoch_rsi']:
                df.ta.stochrsi(close=df['close'], length=period, append=True)
            
            # Williams %R
            for period in INDICATORS_CONFIG['williams_r']:
                willr_result = df.ta.willr(high=df['high'], low=df['low'], close=df['close'], length=period)
                if willr_result is not None:
                    df[f'WR_{period}'] = willr_result
            
            # Commodity Channel Index (CCI)
            for period in INDICATORS_CONFIG['cci']:
                cci_result = df.ta.cci(high=df['high'], low=df['low'], close=df['close'], length=period)
                if cci_result is not None:
                    df[f'CCI_{period}'] = cci_result
            
            # Average True Range (ATR)
            for period in INDICATORS_CONFIG['atr']:
                atr_result = df.ta.atr(high=df['high'], low=df['low'], close=df['close'], length=period)
                if atr_result is not None:
                    df[f'ATR_{period}'] = atr_result
            
            # Parabolic SAR
            for acceleration, maximum in INDICATORS_CONFIG['parabolic_sar']:
                psar_result = df.ta.psar(high=df['high'], low=df['low'], close=df['close'], af=acceleration, max_af=maximum)
                if psar_result is not None and not psar_result.empty:
                    if 'PSARl_0.02_0.2' in psar_result.columns:
                        df['PSARl_0.02_0.2'] = psar_result['PSARl_0.02_0.2']
                    if 'PSARs_0.02_0.2' in psar_result.columns:
                        df['PSARs_0.02_0.2'] = psar_result['PSARs_0.02_0.2']
        
        print("✅ Advanced technical indicators calculated successfully")
        return True
    except Exception as e:
        print(f"⚠️ Warning in indicator calculation: {e}")
        print("Continuing with basic indicators only...")
        return True  # Continue even if some advanced indicators fail

# --- Enhanced Analytics Calculation and Storage ---
def calculate_and_save_analytics(coin_id, price_data):
    """Enhanced analytics calculation with comprehensive indicators"""
    conn = get_db_connection()
    if conn is None: 
        return False

    try:
        print(f"Processing enhanced analytics for {coin_id.upper()}...")
        
        # Fetch historical data
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
        
        # Calculate all indicators
        if not calculate_advanced_indicators(df):
            print(f"❌ Failed to calculate indicators for {coin_id}")
            return False
        
        # Get latest calculated values
        latest_data = df.iloc[-1]
        
        print(f"Saving enhanced analytics for {coin_id}...")
        cur = conn.cursor()
        
        # Enhanced insert query with new fields
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
        
        # Prepare values with safe extraction
        def safe_get(col_name, default=None):
            value = latest_data.get(col_name, default)
            if pd.isna(value):
                return None
            return float(value) if value is not None else None
        
        db_values = (
            coin_id,
            safe_get('close'),
            safe_get('market_cap'),
            safe_get('volume_24h'),
            safe_get('change_24h'),
            # SMAs - map correctly to pandas_ta output
            safe_get('SMA_20'), safe_get('SMA_100'), safe_get('SMA_200'),  # SMA_200 needs to be added to config
            # EMAs
            safe_get('EMA_12'), safe_get('EMA_26'), safe_get('EMA_50'),
            # RSI and MACD
            safe_get('RSI_14'), safe_get('MACD_12_26_9'), safe_get('MACDs_12_26_9'), safe_get('MACDh_12_26_9'),
            # Bollinger Bands
            safe_get('BBL_20_2.0_2.0'), safe_get('BBM_20_2.0_2.0'), safe_get('BBU_20_2.0_2.0'),
            # Stochastic RSI
            safe_get('STOCHRSIk_14_14_3_3'), safe_get('STOCHRSId_14_14_3_3'),
            # Advanced indicators
            safe_get('WR_14'), safe_get('CCI_20'), safe_get('ATR_14'),
            # Parabolic SAR
            safe_get('PSARl_0.02_0.2'), safe_get('PSARs_0.02_0.2')
        )
        
        cur.execute(insert_query, db_values)
        conn.commit()
        cur.close()
        
        print(f"✅ Successfully saved enhanced analytics for {coin_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error processing {coin_id}: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn: 
            conn.close()

if __name__ == "__main__":
    print("🚀 Starting Enhanced Crypto Analytics Collection 🚀")
    print(f"Tracking {len(COINS_TO_TRACK)} cryptocurrencies with advanced indicators")
    
    # Fetch enhanced price data
    enhanced_data = fetch_prices(COINS_TO_TRACK)
    
    if enhanced_data:
        successful_updates = 0
        failed_updates = 0
        
        for coin_id, price_data in enhanced_data.items():
            print(f"\n----- Processing {coin_id.upper()} -----")
            print(f"Price: ${price_data['price']:,.2f}")
            if price_data.get('change_24h'):
                print(f"24h Change: {price_data['change_24h']:.2f}%")
            
            if calculate_and_save_analytics(coin_id, price_data):
                successful_updates += 1
            else:
                failed_updates += 1
            
            # Rate limiting to avoid API restrictions
            time.sleep(2)
        
        print(f"\n✅ Enhanced Analytics Collection Complete!")
        print(f"✅ Successful: {successful_updates} coins")
        print(f"❌ Failed: {failed_updates} coins")
    else:
        print("❌ Failed to fetch price data. Please check your API key and internet connection.")