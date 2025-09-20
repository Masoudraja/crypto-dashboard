# 1. Import necessary libraries
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.sql import SQL, Identifier # For safe dynamic queries
import os
import decimal
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List # For optional query parameters
from dotenv import load_dotenv

# --- Import Automation Controller ---
try:
    from automation_controller import AutomationController
    automation_controller = AutomationController()
except ImportError:
    automation_controller = None

# --- Load Environment Variables ---
load_dotenv()
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# 2. Create a FastAPI app instance
app = FastAPI()

# --- Add CORS Middleware ---
origins = [
    "http://localhost:3000", # The address of our frontend app
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database Connection Function ---
def get_db_connection():
    """Establishes a connection to the database."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

# --- NEW ENDPOINT: Get list of available coins ---
@app.get("/coins")
def get_available_coins():
    """Fetches a list of unique coin IDs from the database."""
    conn = get_db_connection()
    if conn is None: raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cur = conn.cursor()
        query = "SELECT DISTINCT coin_id FROM crypto_prices ORDER BY coin_id;"
        cur.execute(query)
        # The result is a list of tuples, like [('bitcoin',), ('ethereum',)], so we flatten it.
        coins = [item[0] for item in cur.fetchall()]
        cur.close()
        return {"coins": coins}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")
    finally:
        if conn: conn.close()

# --- UPGRADED ENDPOINT: Get prices for a specific coin with timeframe ---
@app.get("/prices/{coin_id}")
def get_prices(coin_id: str, timeframe: Optional[str] = '7d'):
    """Fetches price entries for a specific coin based on a timeframe."""
    conn = get_db_connection()
    if conn is None: raise HTTPException(status_code=500, detail="Database connection failed")
    
    results = []
    try:
        cur = conn.cursor()
        
        # --- Enhanced query to include ALL indicators ---
        base_query = """
            SELECT 
                timestamp, coin_id, price_usd, market_cap, volume_24h, change_24h,
                sma_20, sma_100, sma_200, ema_12, ema_26, ema_50, rsi_14, 
                macd_line, macd_signal, macd_hist,
                bb_lower, bb_mid, bb_upper,
                stochrsi_k, stochrsi_d, williams_r_14, cci_20, atr_14,
                psar_long, psar_short
            FROM crypto_prices 
            WHERE coin_id = %s {timeframe_clause}
            ORDER BY timestamp DESC 
            {limit_clause};
        """
        
        # ... (The rest of the function for timeframe logic remains the same) ...
        timeframe_clause = ""
        limit_clause = "LIMIT 1000"
        
        if timeframe == '24h':
            timeframe_clause = "AND timestamp >= NOW() - INTERVAL '1 day'"
            limit_clause = ""
        elif timeframe == '7d':
            timeframe_clause = "AND timestamp >= NOW() - INTERVAL '7 day'"
            limit_clause = ""
        elif timeframe == '30d':
            timeframe_clause = "AND timestamp >= NOW() - INTERVAL '30 day'"
            limit_clause = ""
        
        final_query = SQL(base_query.format(timeframe_clause=timeframe_clause, limit_clause=limit_clause))
        cur.execute(final_query, (coin_id,))
        
        rows = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]
        
        for row in rows:
            row_dict = dict(zip(colnames, row))
            for key, value in row_dict.items():
                if isinstance(value, decimal.Decimal):
                    row_dict[key] = float(value)
            results.append(row_dict)
            
        cur.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")
    finally:
        if conn: conn.close()
            
    return {"prices": results[::-1]}

# --- UNCHANGED ENDPOINT: Get news ---
@app.get("/news")
def get_news(search: Optional[str] = None, limit: int = 20, offset: int = 0):
    """Fetches news articles with optional search and pagination."""
    conn = get_db_connection()
    if conn is None: raise HTTPException(status_code=500, detail="Database connection failed")
    
    results = []
    try:
        cur = conn.cursor()
        
        # Start with the base query
        base_query = "SELECT title, link, published_date, source FROM news_articles "
        where_clauses = []
        params = []

        # Add a search filter if provided
        if search:
            where_clauses.append("title ILIKE %s")
            params.append(f"%{search}%") # ILIKE is case-insensitive
        
        if where_clauses:
            base_query += "WHERE " + " AND ".join(where_clauses)
        
        # Add ordering, limit, and offset for pagination
        base_query += " ORDER BY published_date DESC LIMIT %s OFFSET %s;"
        params.extend([limit, offset])

        cur.execute(base_query, tuple(params))
        
        rows = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]
        
        for row in rows:
            results.append(dict(zip(colnames, row)))
            
        cur.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")
    finally:
        if conn: conn.close()
            
    return {"articles": results}

# --- UNCHANGED ENDPOINT: Root path ---
@app.get("/")
def read_root():
    return {"status": "Crypto API is running!"}

# --- NEW ENDPOINT: Health Check ---
@app.get("/health")
def health_check():
    """Basic health check endpoint for monitoring."""
    conn = get_db_connection()
    if conn is None:
        return {"status": "unhealthy", "database": "disconnected"}
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM crypto_prices LIMIT 1;")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "total_records": count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "unhealthy", "database": "error", "error": str(e)}

# --- NEW ENDPOINT: Advanced Analytics - Correlation Matrix ---
@app.get("/api/analysis/correlation")
def get_correlation_analysis(days: int = 30):
    """Calculate correlation matrix between cryptocurrencies."""
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cur = conn.cursor()
        
        # Get recent price data for correlation analysis
        query = """
            SELECT coin_id, timestamp, price_usd, change_24h
            FROM crypto_prices 
            WHERE timestamp >= NOW() - INTERVAL %s
            AND price_usd IS NOT NULL
            ORDER BY coin_id, timestamp;
        """
        cur.execute(query, (f'{days} days',))
        rows = cur.fetchall()
        
        if not rows:
            raise HTTPException(status_code=404, detail="No data found for the specified period")
        
        # Organize data by coin
        import pandas as pd
        import numpy as np
        
        # Convert to DataFrame for easier correlation calculation
        df_data = []
        for row in rows:
            df_data.append({
                'coin_id': row[0],
                'timestamp': row[1],
                'price_usd': float(row[2]) if row[2] else None,
                'change_24h': float(row[3]) if row[3] else None
            })
        
        df = pd.DataFrame(df_data)
        
        # Pivot to get prices by coin
        price_pivot = df.pivot_table(
            index='timestamp', 
            columns='coin_id', 
            values='price_usd', 
            aggfunc='last'
        ).fillna(method='ffill').dropna(how='all')
        
        # Calculate correlations
        correlation_matrix = price_pivot.corr()
        
        # Convert to the expected format
        corr_dict = {}
        strongest_correlations = []
        weakest_correlations = []
        
        coins = list(correlation_matrix.columns)
        
        for i, coin1 in enumerate(coins[:10]):  # Limit to top 10 for performance
            corr_dict[coin1] = {}
            for j, coin2 in enumerate(coins[:10]):
                if i != j:
                    corr_value = correlation_matrix.loc[coin1, coin2]
                    if not np.isnan(corr_value):
                        corr_dict[coin1][coin2] = round(float(corr_value), 3)
                        
                        # Track strongest and weakest correlations
                        if i < j:  # Avoid duplicates
                            pair_name = f"{coin1.title()}-{coin2.title()}"
                            corr_data = {"pair": pair_name, "correlation": round(float(corr_value), 3)}
                            
                            if corr_value > 0.7:
                                strongest_correlations.append(corr_data)
                            elif corr_value < 0.3 and corr_value > -0.3:
                                weakest_correlations.append(corr_data)
        
        # Sort correlations
        strongest_correlations.sort(key=lambda x: x['correlation'], reverse=True)
        weakest_correlations.sort(key=lambda x: abs(x['correlation']))
        
        correlation_data = {
            "correlation_matrix": corr_dict,
            "strongest_correlations": strongest_correlations[:5],
            "weakest_correlations": weakest_correlations[:5],
            "analysis_period": f"{days} days",
            "data_points": len(price_pivot),
            "coins_analyzed": len(coins)
        }
        
        cur.close()
        conn.close()
        return correlation_data
        
    except Exception as e:
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

# --- NEW ENDPOINT: Advanced Analytics - Volatility Analysis ---
@app.get("/api/analysis/volatility")
def get_volatility_analysis(days: int = 30):
    """Calculate time-specific volatility metrics for cryptocurrencies."""
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cur = conn.cursor()
        
        # Time-period specific volatility calculation
        query = """
            WITH daily_prices AS (
                SELECT 
                    coin_id,
                    DATE(timestamp) as date,
                    MIN(price_usd) as day_low,
                    MAX(price_usd) as day_high,
                    AVG(price_usd) as day_avg,
                    STDDEV(price_usd) as price_std,
                    COUNT(*) as data_points_per_day,
                    (MAX(price_usd) - MIN(price_usd)) / AVG(price_usd) as daily_range
                FROM crypto_prices 
                WHERE timestamp >= NOW() - INTERVAL '%s days'
                AND price_usd IS NOT NULL
                AND price_usd > 0
                GROUP BY coin_id, DATE(timestamp)
                HAVING COUNT(*) >= 2
            ),
            period_volatility AS (
                SELECT 
                    coin_id,
                    AVG(daily_range) as avg_daily_volatility,
                    STDDEV(daily_range) as volatility_std,
                    MIN(daily_range) as min_daily_range,
                    MAX(daily_range) as max_daily_range,
                    COUNT(*) as trading_days,
                    AVG(price_std / NULLIF(day_avg, 0)) as normalized_std,
                    VARIANCE(daily_range) as volatility_variance,
                    -- Period-specific metrics
                    CASE WHEN %s <= 7 THEN 'Short-term'
                         WHEN %s <= 30 THEN 'Medium-term'
                         ELSE 'Long-term' END as period_type
                FROM daily_prices
                GROUP BY coin_id
                HAVING COUNT(*) >= LEAST(3, %s / 2)
            )
            SELECT 
                coin_id,
                avg_daily_volatility,
                volatility_std,
                min_daily_range,
                max_daily_range,
                trading_days,
                normalized_std,
                volatility_variance,
                period_type
            FROM period_volatility
            ORDER BY avg_daily_volatility DESC
            LIMIT 25;
        """
        
        # Execute with period-specific parameters
        cur.execute(query, (days, days, days, days))
        rows = cur.fetchall()
        
        if not rows:
            cur.close()
            conn.close()
            return {
                "error": f"No volatility data found for the last {days} days",
                "analysis_period": f"{days} days",
                "volatility_data": []
            }
        
        volatility_data = []
        
        for row in rows:
            coin_id, avg_vol, vol_std, min_range, max_range, trading_days, norm_std, vol_var, period_type = row
            
            # Period-adjusted volatility calculations
            daily_vol = float(avg_vol) * 100 if avg_vol else 0
            
            # Time-period specific scaling
            if days <= 7:
                weekly_vol = daily_vol * (days ** 0.5)
                monthly_vol = daily_vol * ((days * 4) ** 0.5)
                period_adjustment = 1.2  # Higher sensitivity for short periods
            elif days <= 30:
                weekly_vol = daily_vol * (7 ** 0.5)
                monthly_vol = daily_vol * (days ** 0.5)
                period_adjustment = 1.0
            else:
                weekly_vol = daily_vol * (7 ** 0.5)
                monthly_vol = daily_vol * (30 ** 0.5)
                period_adjustment = 0.9  # Dampen for long periods
            
            # Dynamic risk level based on period and volatility
            adjusted_vol = daily_vol * period_adjustment
            
            if period_type == 'Short-term':
                risk_thresholds = [4, 10]  # More sensitive for short-term
            elif period_type == 'Medium-term':
                risk_thresholds = [3, 8]   # Standard thresholds
            else:
                risk_thresholds = [2, 6]   # Less sensitive for long-term
            
            if adjusted_vol < risk_thresholds[0]:
                risk_level = "Low"
            elif adjusted_vol < risk_thresholds[1]:
                risk_level = "Medium"
            else:
                risk_level = "High"
            
            # Calculate period-specific volatility score
            max_vol_for_period = 20 if days <= 7 else (15 if days <= 30 else 12)
            volatility_score = min(adjusted_vol / max_vol_for_period, 1.0)
            
            volatility_data.append({
                "coin_id": coin_id,
                "volatility_score": round(volatility_score, 3),
                "daily_volatility": round(daily_vol / 100, 4),
                "weekly_volatility": round(weekly_vol / 100, 4),
                "monthly_volatility": round(monthly_vol / 100, 4),
                "risk_level": risk_level,
                "trading_days": int(trading_days),
                "min_daily_range": round(float(min_range) * 100, 2) if min_range else 0,
                "max_daily_range": round(float(max_range) * 100, 2) if max_range else 0,
                "period_type": period_type,
                "volatility_std": round(float(vol_std) * 100, 2) if vol_std else 0,
                "normalized_volatility": round(float(norm_std) * 100, 2) if norm_std else 0
            })
        
        # Add period-specific metadata
        result = {
            "volatility_data": volatility_data,
            "analysis_period": f"{days} days",
            "period_type": volatility_data[0]["period_type"] if volatility_data else "Unknown",
            "total_coins_analyzed": len(volatility_data),
            "calculation_timestamp": datetime.now().isoformat(),
            "period_start": (datetime.now() - timedelta(days=days)).isoformat(),
            "period_end": datetime.now().isoformat(),
            "risk_distribution": {
                "low": len([v for v in volatility_data if v["risk_level"] == "Low"]),
                "medium": len([v for v in volatility_data if v["risk_level"] == "Medium"]),
                "high": len([v for v in volatility_data if v["risk_level"] == "High"])
            }
        }
        
        cur.close()
        conn.close()
        return result
        
    except Exception as e:
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=f"Volatility analysis failed: {e}")

# --- NEW ENDPOINT: Market Summary ---
@app.get("/api/analysis/market-summary")
def get_market_summary():
    """Get overall market summary and statistics."""
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cur = conn.cursor()
        
        # Get total market statistics
        market_stats_query = """
            WITH latest_data AS (
                SELECT DISTINCT ON (coin_id) 
                    coin_id, 
                    price_usd, 
                    market_cap, 
                    volume_24h, 
                    change_24h,
                    timestamp
                FROM crypto_prices 
                WHERE timestamp >= NOW() - INTERVAL '2 days'
                AND price_usd IS NOT NULL
                ORDER BY coin_id, timestamp DESC
            )
            SELECT 
                COUNT(*) as total_coins,
                SUM(market_cap) as total_market_cap,
                SUM(volume_24h) as total_volume_24h,
                AVG(change_24h) as avg_change_24h,
                MAX(timestamp) as latest_update
            FROM latest_data
            WHERE market_cap IS NOT NULL;
        """
        
        cur.execute(market_stats_query)
        market_stats = cur.fetchone()
        
        # Get top gainers and losers
        gainers_losers_query = """
            WITH latest_data AS (
                SELECT DISTINCT ON (coin_id) 
                    coin_id, 
                    change_24h,
                    timestamp
                FROM crypto_prices 
                WHERE timestamp >= NOW() - INTERVAL '2 days'
                AND change_24h IS NOT NULL
                ORDER BY coin_id, timestamp DESC
            )
            SELECT coin_id, change_24h
            FROM latest_data
            ORDER BY change_24h DESC;
        """
        
        cur.execute(gainers_losers_query)
        change_data = cur.fetchall()
        
        # Get trending coins (most active by volume)
        trending_query = """
            WITH latest_data AS (
                SELECT DISTINCT ON (coin_id) 
                    coin_id, 
                    volume_24h,
                    timestamp
                FROM crypto_prices 
                WHERE timestamp >= NOW() - INTERVAL '2 days'
                AND volume_24h IS NOT NULL
                ORDER BY coin_id, timestamp DESC
            )
            SELECT coin_id
            FROM latest_data
            ORDER BY volume_24h DESC
            LIMIT 5;
        """
        
        cur.execute(trending_query)
        trending_coins = [row[0] for row in cur.fetchall()]
        
        # Process gainers and losers
        top_gainers = []
        top_losers = []
        
        for coin_id, change_24h in change_data:
            if change_24h and change_24h > 0:
                top_gainers.append({
                    "coin_id": coin_id,
                    "change_24h": round(float(change_24h), 2)
                })
            elif change_24h and change_24h < 0:
                top_losers.append({
                    "coin_id": coin_id,
                    "change_24h": round(float(change_24h), 2)
                })
        
        # Sort and limit
        top_gainers.sort(key=lambda x: x['change_24h'], reverse=True)
        top_losers.sort(key=lambda x: x['change_24h'])
        
        # Calculate Fear & Greed Index (simplified calculation)
        avg_change = float(market_stats[3]) if market_stats[3] else 0
        fear_greed_index = max(0, min(100, 50 + (avg_change * 2)))  # Simple calculation
        
        market_summary = {
            "total_market_cap": float(market_stats[1]) if market_stats[1] else 0,
            "total_volume_24h": float(market_stats[2]) if market_stats[2] else 0,
            "fear_greed_index": round(fear_greed_index),
            "trending_coins": trending_coins,
            "top_gainers": top_gainers[:5],
            "top_losers": top_losers[:5],
            "total_coins_tracked": int(market_stats[0]) if market_stats[0] else 0,
            "average_change_24h": round(avg_change, 2),
            "last_updated": market_stats[4].isoformat() if market_stats[4] else None
        }
        
        cur.close()
        conn.close()
        return market_summary
        
    except Exception as e:
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=f"Market summary failed: {e}")

# --- NEW ENDPOINT: Market Sentiment Analysis ---
@app.get("/api/analysis/sentiment")
def get_market_sentiment(days: int = 7):
    """Calculate real-time market sentiment indicators."""
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cur = conn.cursor()
        
        # Multi-factor sentiment calculation
        sentiment_query = """
            WITH recent_data AS (
                SELECT 
                    coin_id,
                    price_usd,
                    change_24h,
                    volume_24h,
                    timestamp,
                    ROW_NUMBER() OVER (PARTITION BY coin_id ORDER BY timestamp DESC) as rn
                FROM crypto_prices 
                WHERE timestamp >= NOW() - INTERVAL '%s days'
                AND price_usd IS NOT NULL
                AND change_24h IS NOT NULL
            ),
            current_prices AS (
                SELECT * FROM recent_data WHERE rn = 1
            ),
            sentiment_factors AS (
                SELECT 
                    COUNT(*) as total_coins,
                    AVG(change_24h) as avg_change,
                    STDDEV(change_24h) as volatility,
                    SUM(CASE WHEN change_24h > 0 THEN 1 ELSE 0 END) as gainers,
                    SUM(CASE WHEN change_24h < 0 THEN 1 ELSE 0 END) as losers,
                    SUM(CASE WHEN change_24h > 5 THEN 1 ELSE 0 END) as strong_gainers,
                    SUM(CASE WHEN change_24h < -5 THEN 1 ELSE 0 END) as strong_losers,
                    AVG(volume_24h) as avg_volume,
                    MAX(change_24h) as max_gain,
                    MIN(change_24h) as max_loss
                FROM current_prices
            )
            SELECT 
                total_coins,
                avg_change,
                volatility,
                gainers,
                losers,
                strong_gainers,
                strong_losers,
                avg_volume,
                max_gain,
                max_loss,
                -- Advanced sentiment indicators
                CASE WHEN gainers > losers * 1.5 THEN 'Bullish'
                     WHEN losers > gainers * 1.5 THEN 'Bearish'
                     ELSE 'Neutral' END as market_mood,
                gainers::float / NULLIF(total_coins, 0) * 100 as gainer_percentage
            FROM sentiment_factors;
        """
        
        cur.execute(sentiment_query, (days,))
        sentiment_row = cur.fetchone()
        
        if not sentiment_row:
            cur.close()
            conn.close()
            return {"error": "No sentiment data available"}
        
        # Unpack sentiment data
        (total_coins, avg_change, volatility, gainers, losers, strong_gainers, 
         strong_losers, avg_volume, max_gain, max_loss, market_mood, gainer_pct) = sentiment_row
        
        # Calculate enhanced Fear & Greed Index
        fear_greed_factors = {
            'price_momentum': min(max((float(avg_change) + 5) / 10 * 100, 0), 100),
            'market_breadth': float(gainer_pct) if gainer_pct else 50,
            'volatility_factor': max(0, min(100, 100 - (float(volatility) * 10))) if volatility else 50,
            'strong_movements': (
                (float(strong_gainers) - float(strong_losers)) / max(float(total_coins), 1) * 100 + 50
            ) if strong_gainers is not None and strong_losers is not None else 50
        }
        
        # Weighted Fear & Greed calculation
        fear_greed_score = (
            fear_greed_factors['price_momentum'] * 0.3 +
            fear_greed_factors['market_breadth'] * 0.25 +
            fear_greed_factors['volatility_factor'] * 0.25 +
            fear_greed_factors['strong_movements'] * 0.2
        )
        
        # Market condition classification
        if fear_greed_score >= 75:
            condition = "Extreme Greed"
            condition_color = "red"
        elif fear_greed_score >= 55:
            condition = "Greed"
            condition_color = "orange"
        elif fear_greed_score >= 45:
            condition = "Neutral"
            condition_color = "gray"
        elif fear_greed_score >= 25:
            condition = "Fear"
            condition_color = "blue"
        else:
            condition = "Extreme Fear"
            condition_color = "green"
        
        # Get trending analysis
        trending_query = """
            SELECT 
                coin_id,
                change_24h,
                volume_24h,
                price_usd
            FROM crypto_prices 
            WHERE timestamp >= NOW() - INTERVAL '6 hours'
            AND change_24h IS NOT NULL
            AND volume_24h IS NOT NULL
            ORDER BY volume_24h DESC
            LIMIT 10;
        """
        
        cur.execute(trending_query)
        trending_coins = [{
            'coin_id': row[0],
            'change_24h': float(row[1]),
            'volume_24h': float(row[2]),
            'price_usd': float(row[3])
        } for row in cur.fetchall()]
        
        sentiment_data = {
            "fear_greed_index": round(fear_greed_score),
            "market_condition": condition,
            "condition_color": condition_color,
            "analysis_period": f"{days} days",
            "market_mood": market_mood,
            "market_statistics": {
                "total_coins_analyzed": int(total_coins),
                "average_change_24h": round(float(avg_change), 2),
                "market_volatility": round(float(volatility), 2) if volatility else 0,
                "gainers": int(gainers),
                "losers": int(losers),
                "gainer_percentage": round(float(gainer_pct), 1),
                "strong_gainers": int(strong_gainers),
                "strong_losers": int(strong_losers)
            },
            "fear_greed_components": {
                "price_momentum": round(fear_greed_factors['price_momentum'], 1),
                "market_breadth": round(fear_greed_factors['market_breadth'], 1),
                "volatility_factor": round(fear_greed_factors['volatility_factor'], 1),
                "strong_movements": round(fear_greed_factors['strong_movements'], 1)
            },
            "trending_by_volume": trending_coins[:5],
            "extreme_performers": {
                "best_performer": {
                    "change": round(float(max_gain), 2),
                    "description": f"+{float(max_gain):.1f}% (24h max gain)"
                },
                "worst_performer": {
                    "change": round(float(max_loss), 2),
                    "description": f"{float(max_loss):.1f}% (24h max loss)"
                }
            },
            "calculation_timestamp": datetime.now().isoformat(),
            "data_freshness": "Real-time"
        }
        
        cur.close()
        conn.close()
        return sentiment_data
        
    except Exception as e:
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {e}")
@app.get("/api/automation/status")
def get_automation_status():
    """Get status of automation tasks and system health."""
    if automation_controller:
        return automation_controller.get_status()
    else:
        # Fallback status when automation controller is not available
        return {
            "tasks": [
                {
                    "task_name": "enhanced_data_collection",
                    "display_name": "Enhanced Data Collection",
                    "status": "stopped",
                    "last_run": None,
                    "next_run": None,
                    "success_count": 0,
                    "error_count": 0,
                    "last_error": None,
                    "interval_minutes": 5
                },
                {
                    "task_name": "news_aggregation",
                    "display_name": "News Aggregation",
                    "status": "stopped",
                    "last_run": None,
                    "next_run": None,
                    "success_count": 0,
                    "error_count": 0,
                    "last_error": None,
                    "interval_minutes": 30
                }
            ],
            "system_health": {
                "database_status": "connected",
                "api_status": "healthy",
                "scheduler_status": "stopped",
                "total_records": 0,
                "latest_update": datetime.now().isoformat(),
                "uptime": "0h 0m"
            },
            "data_stats": {
                "total_price_records": 0,
                "total_news_articles": 0,
                "coins_tracked": 50,
                "last_data_update": datetime.now().isoformat(),
                "update_frequency": "Manual"
            }
        }

# --- NEW ENDPOINT: Start Automation Task ---
@app.post("/api/automation/start/{task_id}")
def start_automation_task(task_id: str):
    """Start a specific automation task."""
    if not automation_controller:
        raise HTTPException(status_code=503, detail="Automation controller not available")
    
    try:
        success = automation_controller.start_task(task_id)
        if success:
            return {"success": True, "message": f"Task {task_id} started successfully"}
        else:
            raise HTTPException(status_code=400, detail=f"Failed to start task {task_id}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting task: {e}")

# --- NEW ENDPOINT: Stop Automation Task ---
@app.post("/api/automation/stop/{task_id}")
def stop_automation_task(task_id: str):
    """Stop a specific automation task."""
    if not automation_controller:
        raise HTTPException(status_code=503, detail="Automation controller not available")
    
    try:
        success = automation_controller.stop_task(task_id)
        if success:
            return {"success": True, "message": f"Task {task_id} stopped successfully"}
        else:
            raise HTTPException(status_code=400, detail=f"Failed to stop task {task_id}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping task: {e}")

# --- NEW ENDPOINT: Run Task Once ---
@app.post("/api/automation/run-once/{task_id}")
def run_task_once(task_id: str):
    """Run a specific task once immediately."""
    if not automation_controller:
        raise HTTPException(status_code=503, detail="Automation controller not available")
    
    try:
        success = automation_controller.run_once(task_id)
        if success:
            return {"success": True, "message": f"Task {task_id} executed successfully"}
        else:
            raise HTTPException(status_code=400, detail=f"Failed to execute task {task_id}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing task: {e}")

# --- WebSocket Connection Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.coin_subscriptions: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, coin_id: str = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        if coin_id:
            if coin_id not in self.coin_subscriptions:
                self.coin_subscriptions[coin_id] = []
            self.coin_subscriptions[coin_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        # Remove from coin subscriptions
        for coin_id, connections in self.coin_subscriptions.items():
            if websocket in connections:
                connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            self.disconnect(websocket)
    
    async def broadcast_to_coin_subscribers(self, coin_id: str, message: dict):
        """Send real-time price update to all subscribers of a specific coin"""
        if coin_id in self.coin_subscriptions:
            disconnected = []
            for connection in self.coin_subscriptions[coin_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    disconnected.append(connection)
            
            # Clean up disconnected connections
            for conn in disconnected:
                self.disconnect(conn)
    
    async def broadcast_market_update(self, message: dict):
        """Send market-wide updates to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# --- WebSocket Endpoint for Real-time Price Updates ---
@app.websocket("/ws/{coin_id}")
async def websocket_endpoint(websocket: WebSocket, coin_id: str):
    print(f"WebSocket connection attempt for {coin_id}")
    
    try:
        await manager.connect(websocket, coin_id)
        print(f"WebSocket connected for {coin_id}")
        
        # Send initial price data
        try:
            initial_data = await get_latest_price_data(coin_id)
            if initial_data:
                await manager.send_personal_message(json.dumps({
                    'type': 'initial_data',
                    'coin_id': coin_id,
                    'data': initial_data
                }), websocket)
                print(f"Sent initial data for {coin_id}")
            else:
                # Send error if no initial data found
                await manager.send_personal_message(json.dumps({
                    'type': 'error',
                    'coin_id': coin_id,
                    'error': f'No data found for {coin_id}'
                }), websocket)
                return
        except Exception as e:
            print(f"Error getting initial data for {coin_id}: {e}")
            await manager.send_personal_message(json.dumps({
                'type': 'error',
                'coin_id': coin_id,
                'error': f'Failed to get initial data: {str(e)}'
            }), websocket)
            return
        
        # Keep connection alive and send periodic updates
        while True:
            try:
                # Check for new price updates every 15 seconds (reduced frequency)
                await asyncio.sleep(15)
                
                latest_data = await get_latest_price_data(coin_id)
                
                if latest_data:
                    await manager.send_personal_message(json.dumps({
                        'type': 'price_update',
                        'coin_id': coin_id,
                        'data': latest_data,
                        'timestamp': datetime.now().isoformat()
                    }), websocket)
                else:
                    print(f"No updated data available for {coin_id}")
                    
            except asyncio.CancelledError:
                print(f"WebSocket cancelled for {coin_id}")
                break
            except Exception as e:
                print(f"Error in WebSocket loop for {coin_id}: {str(e)}")
                # Send error message to client
                try:
                    await manager.send_personal_message(json.dumps({
                        'type': 'error',
                        'coin_id': coin_id,
                        'error': f'Connection error: {str(e)}'
                    }), websocket)
                except:
                    pass
                break
                
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for {coin_id}")
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error for {coin_id}: {str(e)}")
        manager.disconnect(websocket)

# --- Helper function to get latest price data ---
import asyncio
import concurrent.futures

def get_latest_price_data_sync(coin_id: str):
    """Synchronous version of get latest price data"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        cur = conn.cursor()
        query = """
            SELECT 
                timestamp, price_usd, market_cap, volume_24h, change_24h,
                sma_20, ema_50, rsi_14, macd_line, bb_upper, bb_lower
            FROM crypto_prices 
            WHERE coin_id = %s 
            ORDER BY timestamp DESC 
            LIMIT 1;
        """
        
        cur.execute(query, (coin_id,))
        row = cur.fetchone()
        
        if row:
            colnames = [desc[0] for desc in cur.description]
            data = dict(zip(colnames, row))
            
            # Convert decimal values to float
            for key, value in data.items():
                if isinstance(value, decimal.Decimal):
                    data[key] = float(value)
                elif isinstance(value, datetime):
                    data[key] = value.isoformat()
            
            cur.close()
            conn.close()
            return data
        
        cur.close()
        conn.close()
        return None
        
    except Exception as e:
        print(f"Error getting latest price data for {coin_id}: {e}")
        return None

async def get_latest_price_data(coin_id: str):
    """Async wrapper for getting latest price data"""
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(executor, get_latest_price_data_sync, coin_id)

# --- General Market WebSocket ---
@app.websocket("/ws/market")
async def market_websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Send market overview every 30 seconds
            await asyncio.sleep(30)
            
            # Get market overview data
            market_data = await get_market_overview()
            if market_data:
                await manager.send_personal_message(json.dumps({
                    'type': 'market_update',
                    'data': market_data,
                    'timestamp': datetime.now().isoformat()
                }), websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"Market WebSocket error: {e}")
        manager.disconnect(websocket)

# --- Helper function for market overview ---
async def get_market_overview():
    """Get general market overview data"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        cur = conn.cursor()
        
        # Get top 10 coins by market cap with latest data
        query = """
            WITH latest_prices AS (
                SELECT DISTINCT ON (coin_id) 
                    coin_id, price_usd, market_cap, volume_24h, change_24h, timestamp
                FROM crypto_prices 
                WHERE timestamp >= NOW() - INTERVAL '2 hours'
                ORDER BY coin_id, timestamp DESC
            )
            SELECT coin_id, price_usd, market_cap, volume_24h, change_24h
            FROM latest_prices
            WHERE market_cap IS NOT NULL
            ORDER BY market_cap DESC
            LIMIT 10;
        """
        
        cur.execute(query)
        rows = cur.fetchall()
        
        market_data = []
        for row in rows:
            coin_data = {
                'coin_id': row[0],
                'price_usd': float(row[1]) if row[1] else 0,
                'market_cap': float(row[2]) if row[2] else 0,
                'volume_24h': float(row[3]) if row[3] else 0,
                'change_24h': float(row[4]) if row[4] else 0
            }
            market_data.append(coin_data)
        
        cur.close()
        conn.close()
        return market_data
        
    except Exception as e:
        print(f"Error getting market overview: {e}")
        return None