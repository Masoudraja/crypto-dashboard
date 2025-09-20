#!/usr/bin/env python3
"""
Automated Task Scheduler for Crypto Dashboard
Provides multiple scheduling options for automated data updates
"""

import schedule
import time
import subprocess
import sys
import logging
from datetime import datetime, timedelta
from threading import Thread
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CryptoDashboardScheduler:
    """Automated task scheduler for crypto dashboard data updates"""
    
    def __init__(self, project_path: str = None):
        self.project_path = project_path or os.getcwd()
        self.is_running = False
        
    def run_script(self, script_name: str, description: str = ""):
        """Execute a Python script with proper error handling and logging"""
        try:
            script_path = os.path.join(self.project_path, script_name)
            
            if not os.path.exists(script_path):
                logger.error(f"Script not found: {script_path}")
                return False
            
            logger.info(f"🚀 Starting {description or script_name}...")
            
            # Run script in virtual environment if available
            venv_python = os.path.join(self.project_path, 'venv', 'bin', 'python')
            python_cmd = venv_python if os.path.exists(venv_python) else 'python'
            
            result = subprocess.run(
                [python_cmd, script_path],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode == 0:
                logger.info(f"✅ {description or script_name} completed successfully")
                if result.stdout:
                    logger.debug(f"Output: {result.stdout}")
                return True
            else:
                logger.error(f"❌ {description or script_name} failed with return code {result.returncode}")
                if result.stderr:
                    logger.error(f"Error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ {description or script_name} timed out after 10 minutes")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error running {script_name}: {e}")
            return False
    
    def collect_price_data(self):
        """Collect real-time price data with advanced indicators"""
        return self.run_script('main.py', 'Price Data Collection')
    
    def fetch_news(self):
        """Fetch news from multiple sources"""
        return self.run_script('fetch_news.py', 'News Aggregation')
    
    def update_analysis(self):
        """Run advanced market analysis"""
        return self.run_script('advanced_analysis.py', 'Market Analysis Update')
    
    def full_backfill(self):
        """Run complete historical data backfill (weekly task)"""
        return self.run_script('backfill_data.py', 'Historical Data Backfill')
    
    def health_check(self):
        """Perform system health check"""
        try:
            logger.info("🏥 Performing health check...")
            
            # Check database connectivity
            result = subprocess.run(
                ['python', '-c', 'from config import *; import psycopg2; psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD).close(); print("DB OK")'],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info("✅ Database connection healthy")
                return True
            else:
                logger.error(f"❌ Database connection failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False
    
    def setup_schedule(self):
        """Configure the task schedule"""
        logger.info("📅 Setting up automated task schedule...")
        
        # High-frequency updates (every 5 minutes)
        schedule.every(5).minutes.do(self.collect_price_data)
        
        # News updates (every 30 minutes)
        schedule.every(30).minutes.do(self.fetch_news)
        
        # Analysis updates (every hour)
        schedule.every().hour.do(self.update_analysis)
        
        # Health checks (every 4 hours)
        schedule.every(4).hours.do(self.health_check)
        
        # Full backfill (every Sunday at 2 AM)
        schedule.every().sunday.at("02:00").do(self.full_backfill)
        
        # Daily maintenance at 1 AM
        schedule.every().day.at("01:00").do(self.daily_maintenance)
        
        logger.info("""
📋 Schedule configured:
  📊 Price Data: Every 5 minutes
  📰 News Updates: Every 30 minutes  
  📈 Analysis: Every hour
  🏥 Health Check: Every 4 hours
  🔄 Full Backfill: Sundays at 2 AM
  🧹 Maintenance: Daily at 1 AM
        """)
    
    def daily_maintenance(self):
        """Perform daily maintenance tasks"""
        logger.info("🧹 Running daily maintenance...")
        
        # Clean old log files (keep last 7 days)
        try:
            log_files = Path(self.project_path).glob('*.log')
            cutoff_date = datetime.now() - timedelta(days=7)
            
            for log_file in log_files:
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    logger.info(f"🗑️ Cleaned old log file: {log_file.name}")
        except Exception as e:
            logger.error(f"❌ Error during log cleanup: {e}")
        
        # Database maintenance could be added here
        logger.info("✅ Daily maintenance completed")
    
    def run_scheduler(self):
        """Run the task scheduler continuously"""
        self.setup_schedule()
        self.is_running = True
        
        logger.info("🚀 Crypto Dashboard Scheduler started!")
        logger.info("Press Ctrl+C to stop the scheduler")
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(10)  # Check every 10 seconds
                
        except KeyboardInterrupt:
            logger.info("🛑 Scheduler stopped by user")
            self.is_running = False
        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}")
            self.is_running = False
    
    def run_single_task(self, task_name: str):
        """Run a single task manually"""
        tasks = {
            'price': self.collect_price_data,
            'news': self.fetch_news,
            'analysis': self.update_analysis,
            'backfill': self.full_backfill,
            'health': self.health_check,
            'maintenance': self.daily_maintenance
        }
        
        if task_name in tasks:
            logger.info(f"🎯 Running single task: {task_name}")
            success = tasks[task_name]()
            if success:
                logger.info(f"✅ Task {task_name} completed successfully")
            else:
                logger.error(f"❌ Task {task_name} failed")
            return success
        else:
            logger.error(f"❌ Unknown task: {task_name}")
            logger.info(f"Available tasks: {list(tasks.keys())}")
            return False

def main():
    """Main entry point for the scheduler"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Crypto Dashboard Task Scheduler')
    parser.add_argument('--task', type=str, help='Run a single task (price, news, analysis, backfill, health, maintenance)')
    parser.add_argument('--daemon', action='store_true', help='Run as continuous scheduler daemon')
    parser.add_argument('--path', type=str, help='Project path (default: current directory)')
    
    args = parser.parse_args()
    
    scheduler = CryptoDashboardScheduler(args.path)
    
    if args.task:
        # Run single task
        success = scheduler.run_single_task(args.task)
        sys.exit(0 if success else 1)
    elif args.daemon:
        # Run as daemon
        scheduler.run_scheduler()
    else:
        # Interactive mode
        print("🤖 Crypto Dashboard Task Scheduler")
        print("=" * 50)
        print("1. Run continuous scheduler")
        print("2. Run single task")
        print("3. Show schedule")
        print("4. Exit")
        
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == '1':
            scheduler.run_scheduler()
        elif choice == '2':
            tasks = ['price', 'news', 'analysis', 'backfill', 'health', 'maintenance']
            print(f"\nAvailable tasks: {', '.join(tasks)}")
            task = input("Enter task name: ").strip()
            scheduler.run_single_task(task)
        elif choice == '3':
            scheduler.setup_schedule()
            print("\n📋 Current schedule:")
            for job in schedule.jobs:
                print(f"  {job}")
        else:
            print("👋 Goodbye!")

if __name__ == "__main__":
    main()