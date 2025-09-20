#!/usr/bin/env python3
"""
Advanced Crypto Analysis Tools
Provides sophisticated analysis functions including correlation matrix, volatility analysis, 
momentum scoring, and technical indicators scoring for comprehensive market insights.
"""

import pandas as pd
import numpy as np
from scipy import stats
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, COINS_TO_TRACK

class CryptoAnalysisEngine:
    """Advanced cryptocurrency analysis engine"""
    
    def __init__(self):
        self.coins = COINS_TO_TRACK[:10]  # Limit for performance
        
    def get_db_connection(self):
        """Establish database connection"""
        try:
            return psycopg2.connect(
                host=DB_HOST, port=DB_PORT, dbname=DB_NAME, 
                user=DB_USER, password=DB_PASSWORD
            )
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            return None
    
    def fetch_price_data(self, days: int = 30) -> pd.DataFrame:
        """Fetch price data for analysis"""
        conn = self.get_db_connection()
        if conn is None:
            return pd.DataFrame()
        
        try:
            # Fetch data for multiple coins
            query = """
                SELECT coin_id, timestamp, price_usd, volume_24h, change_24h
                FROM crypto_prices 
                WHERE coin_id = ANY(%s) 
                AND timestamp >= NOW() - INTERVAL '%s days'
                ORDER BY coin_id, timestamp
            """
            
            df = pd.read_sql_query(query, conn, params=(self.coins, days))
            conn.close()
            
            print(f"📊 Fetched {len(df)} price records for analysis")
            return df
            
        except Exception as e:
            print(f"❌ Error fetching price data: {e}")
            if conn:
                conn.close()
            return pd.DataFrame()
    
    def calculate_correlation_matrix(self, days: int = 30) -> Dict[str, Any]:
        """Calculate price correlation matrix between cryptocurrencies"""
        print("🔗 Calculating correlation matrix...")
        
        df = self.fetch_price_data(days)
        if df.empty:
            return {'error': 'No data available'}
        
        # Pivot data to have coins as columns
        price_matrix = df.pivot(index='timestamp', columns='coin_id', values='price_usd')
        
        # Calculate correlation matrix
        correlation_matrix = price_matrix.corr()
        
        # Convert to dictionary format for API response
        correlations = {}
        for coin1 in correlation_matrix.index:
            correlations[coin1] = {}
            for coin2 in correlation_matrix.columns:
                corr_value = correlation_matrix.loc[coin1, coin2]
                if not np.isnan(corr_value):
                    correlations[coin1][coin2] = round(float(corr_value), 4)
        
        # Find highest and lowest correlations
        high_correlations = []
        low_correlations = []
        
        for coin1 in correlations:
            for coin2 in correlations[coin1]:
                if coin1 != coin2:
                    corr_val = correlations[coin1][coin2]
                    if corr_val > 0.8:
                        high_correlations.append((coin1, coin2, corr_val))
                    elif corr_val < 0.2:
                        low_correlations.append((coin1, coin2, corr_val))
        
        return {
            'correlation_matrix': correlations,
            'analysis_period_days': days,
            'high_correlations': sorted(high_correlations, key=lambda x: x[2], reverse=True)[:10],
            'low_correlations': sorted(low_correlations, key=lambda x: x[2])[:10],
            'coins_analyzed': list(price_matrix.columns),
            'timestamp': datetime.now().isoformat()
        }
    
    def calculate_volatility_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Calculate volatility metrics for all tracked coins"""
        print("📈 Calculating volatility analysis...")
        
        df = self.fetch_price_data(days)
        if df.empty:
            return {'error': 'No data available'}
        
        volatility_data = {}
        
        for coin in self.coins:
            coin_data = df[df['coin_id'] == coin].copy()
            if len(coin_data) < 2:
                continue
                
            # Calculate daily returns
            coin_data = coin_data.sort_values('timestamp')
            coin_data['daily_return'] = coin_data['price_usd'].pct_change()
            
            # Volatility metrics
            daily_returns = coin_data['daily_return'].dropna()
            
            if len(daily_returns) > 0:
                volatility_data[coin] = {
                    'daily_volatility': float(daily_returns.std()),
                    'annualized_volatility': float(daily_returns.std() * np.sqrt(365)),
                    'max_daily_gain': float(daily_returns.max()),
                    'max_daily_loss': float(daily_returns.min()),
                    'volatility_rank': 0,  # Will be calculated after all coins
                    'risk_score': float(abs(daily_returns.std()) * 100),
                    'price_range_pct': float((coin_data['price_usd'].max() - coin_data['price_usd'].min()) / coin_data['price_usd'].mean() * 100)
                }
        
        # Rank coins by volatility
        sorted_by_vol = sorted(volatility_data.items(), key=lambda x: x[1]['daily_volatility'], reverse=True)
        for i, (coin, data) in enumerate(sorted_by_vol):
            volatility_data[coin]['volatility_rank'] = i + 1
        
        return {
            'volatility_analysis': volatility_data,
            'analysis_period_days': days,
            'most_volatile': sorted_by_vol[:5],
            'least_volatile': sorted_by_vol[-5:],
            'timestamp': datetime.now().isoformat()
        }

# Example usage
if __name__ == "__main__":
    print("🔬 Testing Advanced Crypto Analysis Tools")
    print("=" * 60)
    
    engine = CryptoAnalysisEngine()
    
    # Test correlation analysis
    print("\n1. Testing Correlation Analysis...")
    correlation_result = engine.calculate_correlation_matrix(7)
    if 'correlation_matrix' in correlation_result:
        print(f"✅ Correlation analysis complete - {len(correlation_result['coins_analyzed'])} coins")
        print(f"Sample correlations: {list(correlation_result['correlation_matrix'].keys())[:3]}")
    else:
        print(f"❌ Correlation analysis failed: {correlation_result}")
    
    # Test volatility analysis
    print("\n2. Testing Volatility Analysis...")
    volatility_result = engine.calculate_volatility_analysis(7)
    if 'volatility_analysis' in volatility_result:
        print(f"✅ Volatility analysis complete")
        if volatility_result['most_volatile']:
            print(f"Most volatile: {volatility_result['most_volatile'][0][0]}")
    else:
        print(f"❌ Volatility analysis failed: {volatility_result}")
    
    print("\n🎯 Advanced analysis tools test complete!")