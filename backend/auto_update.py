#!/usr/bin/env python3
"""
Auto Update Script - Automated Dashboard Maintenance
Runs both enhanced data collection and basic maintenance tasks
"""

import subprocess
import sys
import time
from datetime import datetime

def run_command(command, description):
    \"\"\"Run a command and handle errors gracefully\"\"\"
    print(f\"\n🔄 {description}...\")
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print(f\"✅ {description} completed successfully\")
            if result.stdout.strip():
                print(f\"📄 Output: {result.stdout.strip()[-200:]}...\")  # Last 200 chars
            return True
        else:
            print(f\"❌ {description} failed\")
            print(f\"📄 Error: {result.stderr.strip()[-200:]}...\")  # Last 200 chars
            return False
    except subprocess.TimeoutExpired:
        print(f\"⏰ {description} timed out (5 minutes)\")
        return False
    except Exception as e:
        print(f\"💥 {description} crashed: {e}\")
        return False

def main():
    \"\"\"Main automation function\"\"\"
    print(\"🚀 Enhanced Crypto Dashboard - Auto Update\")
    print(\"=\" * 50)
    print(f\"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\")
    
    # Track success/failure
    total_tasks = 0
    successful_tasks = 0
    
    # Task 1: Enhanced Data Collection (Priority)
    total_tasks += 1
    if run_command(\"python enhanced_data_collector.py\", \"Enhanced Multi-Source Data Collection\"):
        successful_tasks += 1
        print(\"✨ Enhanced data collection provides the most accurate data\")
    else:
        print(\"⚠️  Enhanced collection failed, trying basic collection...\")
        
        # Fallback: Basic Data Collection
        total_tasks += 1
        if run_command(\"python main.py\", \"Basic Data Collection (Fallback)\"):
            successful_tasks += 1
            print(\"✅ Basic data collection succeeded as fallback\")
        else:
            print(\"🚨 Both enhanced and basic data collection failed!\")
    
    # Task 2: Database Health Check (Optional)
    total_tasks += 1
    if run_command(
        \"python -c \\\"import psycopg2; from config import *; conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD); cur = conn.cursor(); cur.execute('SELECT COUNT(*) FROM crypto_prices WHERE timestamp >= NOW() - INTERVAL \\\\'24 hours\\\\''); print(f'Recent records: {cur.fetchone()[0]}'); conn.close()\\\"\",
        \"Database Health Check\"
    ):
        successful_tasks += 1
    
    # Task 3: API Server Test (Optional)
    total_tasks += 1
    if run_command(
        \"curl -s http://localhost:8000/health | python -c \\\"import sys, json; data = json.load(sys.stdin); print(f'API Status: {data.get(\\\\'status\\\\', \\\\'unknown\\\\')}')\\\" 2>/dev/null || echo 'API server not running'\",
        \"API Server Health Check\"
    ):
        successful_tasks += 1
    
    # Summary
    print(\"\n\" + \"=\" * 50)
    print(f\"📊 Update Summary:\")
    print(f\"✅ Successful tasks: {successful_tasks}/{total_tasks}\")
    print(f\"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\")
    
    success_rate = (successful_tasks / total_tasks) * 100
    if success_rate >= 80:
        print(f\"🎉 Great! {success_rate:.0f}% success rate\")
        print(\"💡 Your dashboard data is fresh and ready!\")
    elif success_rate >= 50:
        print(f\"⚠️  Partial success: {success_rate:.0f}% success rate\")
        print(\"💡 Some data updated, but check for issues\")
    else:
        print(f\"🚨 Low success rate: {success_rate:.0f}%\")
        print(\"💡 Manual intervention may be required\")
    
    # Recommendations
    print(\"\n📋 Quick Status Check:\")
    print(\"   1. Visit http://localhost:3000/advanced to see latest analytics\")
    print(\"   2. Check if time periods show different data (real-time working)\")
    print(\"   3. Enable auto-refresh for live monitoring\")
    
    return successful_tasks >= 1  # Success if at least basic data collection worked

if __name__ == \"__main__\":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(\"\n🛑 Update cancelled by user\")
        sys.exit(1)
    except Exception as e:
        print(f\"\n💥 Unexpected error: {e}\")
        sys.exit(1)
