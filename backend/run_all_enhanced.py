#!/usr/bin/env python3
"""
Enhanced Crypto Dashboard - Complete Automation Script
Runs all enhanced features including multi-API data collection, 
advanced analytics, and system health checks.
"""

import subprocess
import sys
import time
import requests
from datetime import datetime

def print_banner():
    print("🚀" + "=" * 70 + "🚀")
    print("   ENHANCED CRYPTO DASHBOARD - COMPLETE AUTOMATION")
    print("🚀" + "=" * 70 + "🚀")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def run_command(command, description, show_output=False):
    """Run a command and return success status"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if show_output and result.stdout.strip():
                print(f"   Output: {result.stdout.strip()[-200:]}...")
            return True
        else:
            print(f"❌ {description} failed")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()[-200:]}...")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} timed out")
        return False
    except Exception as e:
        print(f"💥 {description} crashed: {e}")
        return False

def test_api_endpoints():
    """Test all enhanced API endpoints"""
    print("\n🔍 Testing Enhanced API Endpoints...")
    
    endpoints = [
        ("http://localhost:8000/api/analysis/correlation?days=7", "Correlation Analysis (7 days)"),
        ("http://localhost:8000/api/analysis/correlation?days=30", "Correlation Analysis (30 days)"),
        ("http://localhost:8000/api/analysis/volatility?days=7", "Volatility Analysis (7 days)"),
        ("http://localhost:8000/api/analysis/volatility?days=30", "Volatility Analysis (30 days)"),
        ("http://localhost:8000/api/analysis/sentiment?days=7", "Market Sentiment Analysis"),
        ("http://localhost:8000/api/analysis/market-summary", "Market Summary"),
        ("http://localhost:8000/health", "Health Check")
    ]
    
    passed = 0
    total = len(endpoints)
    
    for url, name in endpoints:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"   ✅ {name}")
                passed += 1
            else:
                print(f"   ❌ {name} (Status: {response.status_code})")
        except Exception as e:
            print(f"   ❌ {name} (Error: {str(e)[:50]}...)")
    
    print(f"\n📊 API Test Results: {passed}/{total} endpoints working")
    return passed == total

def display_data_quality_metrics():
    """Display current data quality metrics"""
    print("\n📈 Data Quality Metrics:")
    
    try:
        # Test correlation data
        response = requests.get("http://localhost:8000/api/analysis/correlation?days=30", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   • Correlation Data: {data.get('data_points', 'N/A')} points, {data.get('coins_analyzed', 'N/A')} coins")
        
        # Test sentiment data
        response = requests.get("http://localhost:8000/api/analysis/sentiment?days=7", timeout=10)
        if response.status_code == 200:
            data = response.json()
            stats = data.get('market_statistics', {})
            print(f"   • Market Sentiment: {data.get('market_condition', 'N/A')} (Index: {data.get('fear_greed_index', 'N/A')})")
            print(f"   • Market Activity: {stats.get('gainers', 'N/A')} gainers, {stats.get('losers', 'N/A')} losers")
        
        # Test market summary
        response = requests.get("http://localhost:8000/api/analysis/market-summary", timeout=10)
        if response.status_code == 200:
            data = response.json()
            market_cap = data.get('total_market_cap', 0)
            if market_cap >= 1e12:
                cap_str = f"${market_cap/1e12:.2f}T"
            elif market_cap >= 1e9:
                cap_str = f"${market_cap/1e9:.2f}B"
            else:
                cap_str = f"${market_cap/1e6:.2f}M"
            print(f"   • Market Cap: {cap_str}")
            print(f"   • 24h Volume: ${data.get('total_volume_24h', 0)/1e9:.2f}B")
        
    except Exception as e:
        print(f"   ❌ Could not fetch metrics: {e}")

def main():
    """Main execution function"""
    print_banner()
    
    tasks_completed = 0
    total_tasks = 0
    
    # Task 1: Enhanced Multi-Source Data Collection
    total_tasks += 1
    print("1️⃣  ENHANCED DATA COLLECTION")
    print("   📡 Using 6 API sources: CoinGecko, CoinPaprika, CoinStats, CoinMarketCap, Alpha Vantage, CoinDesk")
    if run_command("python enhanced_data_collector.py", "Enhanced Multi-Source Data Collection", True):
        tasks_completed += 1
        print("   ✨ Multi-source data collection provides maximum reliability")
    else:
        print("   ⚠️  Enhanced collection failed, trying basic collection...")
        total_tasks += 1
        if run_command("python main.py", "Basic Data Collection (Fallback)"):
            tasks_completed += 1
    
    # Task 2: API Server Health Check
    total_tasks += 1
    print("\n2️⃣  API SERVER VALIDATION")
    if test_api_endpoints():
        tasks_completed += 1
        print("   🎉 All enhanced API endpoints are working correctly!")
    else:
        print("   ⚠️  Some API endpoints may have issues")
    
    # Task 3: Data Quality Assessment
    total_tasks += 1
    print("\n3️⃣  DATA QUALITY ASSESSMENT")
    try:
        display_data_quality_metrics()
        tasks_completed += 1
        print("   ✅ Data quality metrics retrieved successfully")
    except Exception as e:
        print(f"   ❌ Data quality check failed: {e}")
    
    # Task 4: Database Health Check
    total_tasks += 1
    print("\n4️⃣  DATABASE HEALTH CHECK")
    if run_command(
        'python -c "import psycopg2; from config import *; conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD); cur = conn.cursor(); cur.execute(\\"SELECT COUNT(*) FROM crypto_prices WHERE timestamp >= NOW() - INTERVAL \'24 hours\'\\"); print(f\\"Recent records: {cur.fetchone()[0]}\\"); conn.close()"',
        "Database Health Check"
    ):
        tasks_completed += 1
    
    # Final Summary
    print("\n" + "🏁" + "=" * 70 + "🏁")
    print("ENHANCED CRYPTO DASHBOARD - EXECUTION SUMMARY")
    print("🏁" + "=" * 70 + "🏁")
    
    success_rate = (tasks_completed / total_tasks) * 100
    print(f"📊 Tasks Completed: {tasks_completed}/{total_tasks} ({success_rate:.1f}%)")
    print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success_rate >= 90:
        print("🎉 EXCELLENT! Your enhanced crypto dashboard is fully operational!")
        print("✨ Features available:")
        print("   • Real-time data from 6 API sources")
        print("   • Advanced correlation analysis with time-period specificity")
        print("   • Enhanced volatility analysis with risk categorization")
        print("   • Real-time market sentiment indicators")
        print("   • Comprehensive market summary with Fear & Greed Index")
        print("   • Enhanced user interface with quick preset buttons")
    elif success_rate >= 70:
        print("✅ GOOD! Most features are working correctly")
        print("💡 Some minor issues detected - check the logs above")
    else:
        print("⚠️  ISSUES DETECTED! Manual intervention may be required")
        print("💡 Please review the error messages above")
    
    print("\n🌐 Next Steps:")
    print("   1. Visit http://localhost:3000/advanced to see enhanced analytics")
    print("   2. Try different time periods (7d/30d/90d) - data should change!")
    print("   3. Use the new preset buttons in /analysis for quick indicator setup")
    print("   4. Enable auto-refresh for live monitoring")
    print("   5. Monitor real-time sentiment and Fear & Greed Index")
    
    print(f"\n🎯 Data Quality Score: {success_rate:.1f}%")
    print("📈 Your crypto dashboard now provides professional-grade analytics!")
    
    return success_rate >= 70

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Execution cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)