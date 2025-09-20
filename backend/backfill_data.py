# File: backfill_data.py
import requests
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
import pandas_ta as ta
import time
from datetime import datetime, timedelta
from config import COINS_TO_TRACK, API_KEY, DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

DAYS_TO_BACKFILL = 180

def get_db_connection():
    try:
        return psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def backfill_historical_data():
    print(f"--- Starting historical backfill for last {DAYS_TO_BACKFILL} days ---")
    conn = get_db_connection()
    if conn is None: return

    end_date = datetime.now()
    start_date = end_date - timedelta(days=DAYS_TO_BACKFILL)
    from_timestamp, to_timestamp = int(start_date.timestamp()), int(end_date.timestamp())

    for coin_id in COINS_TO_TRACK:
        print(f"\n----- Processing {coin_id.upper()} -----")
        try:
            cur = conn.cursor()
            print(f"1. Clearing old data for {coin_id}...")
            cur.execute("DELETE FROM crypto_prices WHERE coin_id = %s;", (coin_id,))
            
            print("2. Fetching historical data from API...")
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart/range"
            params = { 'vs_currency': 'usd', 'from': from_timestamp, 'to': to_timestamp, 'x_cg_demo_api_key': API_KEY }
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if not data.get('prices'):
                print(f"--> No historical data found for {coin_id}. Skipping.")
                continue

            df = pd.DataFrame(data['prices'], columns=['timestamp_ms', 'close'])
            df['timestamp'] = pd.to_datetime(df['timestamp_ms'], unit='ms', utc=True)
            df.set_index('timestamp', inplace=True)
            df.drop('timestamp_ms', axis=1, inplace=True)

            print(f"3. Calculating all technical indicators for {len(df)} data points...")
            # Calculate indicators individually like in main.py
            df.ta.sma(close=df['close'], length=20, append=True)
            df.ta.ema(close=df['close'], length=50, append=True)
            df.ta.rsi(close=df['close'], append=True)
            df.ta.macd(close=df['close'], append=True)
            df.ta.bbands(close=df['close'], length=20, append=True)
            print("[DEBUG] Columns available after calculation:", df.columns.tolist())

            print("4. Preparing data for insertion...")
            records_to_insert = []
            for timestamp, row in df.iterrows():
                record = tuple(
                    [coin_id, timestamp] + 
                    [float(row.get(col)) if pd.notna(row.get(col)) else None for col in [
                        'close', 'SMA_20', 'EMA_50', 'RSI_14', 'MACD_12_26_9', 
                        'MACDs_12_26_9', 'MACDh_12_26_9', 'BBL_20_2.0_2.0', 
                        'BBM_20_2.0_2.0', 'BBU_20_2.0_2.0'
                    ]]
                )
                records_to_insert.append(record)
            
            print(f"5. Inserting {len(records_to_insert)} records into database...")
            insert_query = "INSERT INTO crypto_prices (coin_id, timestamp, price_usd, sma_20, ema_50, rsi_14, macd_line, macd_signal, macd_hist, bb_lower, bb_mid, bb_upper) VALUES %s;"
            execute_values(cur, insert_query, records_to_insert)
            
            conn.commit()
            print(f"✅ COMMIT successful for {coin_id}.")
            cur.close()
            time.sleep(5)
        except Exception as e:
            print(f"❌ An error occurred while processing {coin_id}: {e}")
            conn.rollback()
            continue
    conn.close()
    print("\n--- Historical data backfill process finished ---")

if __name__ == "__main__":
    backfill_historical_data()