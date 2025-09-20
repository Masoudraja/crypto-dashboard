#!/usr/bin/env python3
"""
Real-Time Automation Controller for Crypto Dashboard
Provides actual play/stop controls and continuous data updates
"""

import asyncio
import json
import time
import subprocess
import threading
import signal
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import psutil

class AutomationController:
    def __init__(self):
        self.tasks = {
            "enhanced_data_collection": {
                "name": "Enhanced Data Collection",
                "script": "enhanced_data_collector.py",
                "interval": 300,  # 5 minutes
                "status": "stopped",
                "last_run": None,
                "next_run": None,
                "success_count": 0,
                "error_count": 0,
                "last_error": None,
                "process": None,
                "thread": None
            },
            "news_aggregation": {
                "name": "News Aggregation",
                "script": "fetch_news.py", 
                "interval": 1800,  # 30 minutes
                "status": "stopped",
                "last_run": None,
                "next_run": None,
                "success_count": 0,
                "error_count": 0,
                "last_error": None,
                "process": None,
                "thread": None
            },
            "market_analysis": {
                "name": "Market Analysis",
                "script": "advanced_analysis.py",
                "interval": 3600,  # 1 hour
                "status": "stopped", 
                "last_run": None,
                "next_run": None,
                "success_count": 0,
                "error_count": 0,
                "last_error": None,
                "process": None,
                "thread": None
            }
        }
        
        self.is_running = False
        self.start_time = datetime.now()
        
    def run_script(self, script_name: str, task_id: str) -> bool:
        """Execute a script and update task statistics"""
        try:
            print(f"🔄 Running {script_name}...")
            
            # Update task status
            self.tasks[task_id]["last_run"] = datetime.now().isoformat()
            self.tasks[task_id]["status"] = "running"
            
            # Execute script
            result = subprocess.run(
                [sys.executable, script_name],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            if result.returncode == 0:
                self.tasks[task_id]["success_count"] += 1
                self.tasks[task_id]["last_error"] = None
                print(f"✅ {script_name} completed successfully")
                return True
            else:
                self.tasks[task_id]["error_count"] += 1
                self.tasks[task_id]["last_error"] = result.stderr[:200] if result.stderr else "Unknown error"
                print(f"❌ {script_name} failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.tasks[task_id]["error_count"] += 1
            self.tasks[task_id]["last_error"] = "Script timed out after 10 minutes"
            print(f"⏰ {script_name} timed out")
            return False
        except Exception as e:
            self.tasks[task_id]["error_count"] += 1
            self.tasks[task_id]["last_error"] = str(e)[:200]
            print(f"💥 Error running {script_name}: {e}")
            return False
        finally:
            # Always update status and next run time
            if task_id in self.tasks:
                # For continuous tasks, set back to running if it was running
                # For one-time runs, set to stopped
                if self.tasks[task_id]["status"] == "running":
                    # Keep running status for continuous tasks
                    pass
                else:
                    # Set to stopped for one-time runs
                    self.tasks[task_id]["status"] = "stopped"
                    
                interval = self.tasks[task_id]["interval"]
                self.tasks[task_id]["next_run"] = (datetime.now() + timedelta(seconds=interval)).isoformat()
    
    def task_worker(self, task_id: str):
        """Worker thread for continuous task execution"""
        task = self.tasks[task_id]
        
        while task["status"] == "running":
            try:
                # Run the script
                success = self.run_script(task["script"], task_id)
                
                # Wait for next execution
                interval = task["interval"]
                for _ in range(interval):
                    if task["status"] != "running":
                        break
                    time.sleep(1)
                        
            except Exception as e:
                print(f"❌ Task worker error for {task_id}: {e}")
                task["status"] = "error"
                task["last_error"] = str(e)
                break
    
    def start_task(self, task_id: str) -> bool:
        """Start a specific task"""
        if task_id not in self.tasks:
            return False
            
        task = self.tasks[task_id]
        
        if task["status"] == "running":
            print(f"⚠️  Task {task_id} is already running")
            return True
            
        try:
            # Update status
            task["status"] = "running"
            task["next_run"] = (datetime.now() + timedelta(seconds=task["interval"])).isoformat()
            
            # Start worker thread
            thread = threading.Thread(target=self.task_worker, args=(task_id,))
            thread.daemon = True
            thread.start()
            task["thread"] = thread
            
            print(f"▶️  Started task: {task['name']}")
            return True
            
        except Exception as e:
            task["status"] = "error"
            task["last_error"] = str(e)
            print(f"❌ Failed to start task {task_id}: {e}")
            return False
    
    def stop_task(self, task_id: str) -> bool:
        """Stop a specific task"""
        if task_id not in self.tasks:
            return False
            
        task = self.tasks[task_id]
        
        try:
            # Update status to stop the worker loop
            task["status"] = "stopped"
            task["next_run"] = None
            
            # Wait for thread to finish (with timeout)
            if task["thread"] and task["thread"].is_alive():
                task["thread"].join(timeout=5)
                
            task["thread"] = None
            print(f"⏹️  Stopped task: {task['name']}")
            return True
            
        except Exception as e:
            print(f"❌ Error stopping task {task_id}: {e}")
            return False
    
    def start_all_tasks(self):
        """Start all automation tasks"""
        print("🚀 Starting all automation tasks...")
        self.is_running = True
        
        for task_id in self.tasks:
            self.start_task(task_id)
            
        print("✅ All tasks started")
    
    def stop_all_tasks(self):
        """Stop all automation tasks"""
        print("🛑 Stopping all automation tasks...")
        self.is_running = False
        
        for task_id in self.tasks:
            self.stop_task(task_id)
            
        print("✅ All tasks stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current automation status"""
        # Calculate system stats
        try:
            # Get database record count for crypto prices, news, and unique coins
            query_script = """
import psycopg2
from config import *
conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM crypto_prices')
price_count = cur.fetchone()[0]
try:
    cur.execute('SELECT COUNT(*) FROM news_articles')
    news_count = cur.fetchone()[0]
except:
    news_count = 0
try:
    cur.execute('SELECT COUNT(DISTINCT coin_id) FROM crypto_prices')
    coins_count = cur.fetchone()[0]
except:
    coins_count = 0
print(f'{price_count},{news_count},{coins_count}')
conn.close()
"""
            
            result = subprocess.run(
                [sys.executable, "-c", query_script],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            if result.returncode == 0:
                counts = result.stdout.strip().split(',')
                total_records = int(counts[0]) if len(counts) > 0 else 0
                news_count = int(counts[1]) if len(counts) > 1 else 0
                coins_tracked = int(counts[2]) if len(counts) > 2 else 0
            else:
                print(f"Database query error: {result.stderr}")
                total_records = 0
                news_count = 0
                coins_tracked = 0
        except Exception as e:
            print(f"Database query exception: {e}")
            total_records = 0
            news_count = 0
            coins_tracked = 0
        
        # Calculate uptime
        uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        uptime_str = f"{hours}h {minutes}m"
        
        # Check if any tasks are running
        running_tasks = [task for task in self.tasks.values() if task["status"] == "running"]
        scheduler_status = "running" if running_tasks else "stopped"
        
        # Get latest update time from successful runs
        latest_update = None
        for task in self.tasks.values():
            if task["last_run"]:
                if not latest_update or task["last_run"] > latest_update:
                    latest_update = task["last_run"]
        
        if not latest_update:
            latest_update = datetime.now().isoformat()
        
        return {
            "tasks": [
                {
                    "task_name": task_id,
                    "display_name": task_data["name"],
                    "status": task_data["status"],
                    "last_run": task_data["last_run"],
                    "next_run": task_data["next_run"],
                    "success_count": task_data["success_count"],
                    "error_count": task_data["error_count"],
                    "last_error": task_data["last_error"],
                    "interval_minutes": task_data["interval"] // 60
                }
                for task_id, task_data in self.tasks.items()
            ],
            "system_health": {
                "database_status": "connected" if total_records > 0 else "disconnected",
                "api_status": "healthy",
                "scheduler_status": scheduler_status,
                "total_records": total_records,
                "latest_update": latest_update,
                "uptime": uptime_str
            },
            "data_stats": {
                "total_price_records": total_records,
                "total_news_articles": news_count,
                "coins_tracked": coins_tracked,
                "last_data_update": latest_update,
                "update_frequency": "5 minutes" if running_tasks else "Manual"
            }
        }
    
    def run_once(self, task_id: str) -> bool:
        """Run a task once immediately without affecting continuous scheduling"""
        if task_id not in self.tasks:
            return False
            
        task = self.tasks[task_id]
        print(f"🎯 Running {task['name']} once...")
        
        # Save current status
        original_status = task["status"]
        
        try:
            # Temporarily update for execution tracking
            task["last_run"] = datetime.now().isoformat()
            
            # Execute script directly
            result = subprocess.run(
                [sys.executable, task["script"]],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            if result.returncode == 0:
                task["success_count"] += 1
                task["last_error"] = None
                print(f"✅ {task['script']} completed successfully")
                return True
            else:
                task["error_count"] += 1
                task["last_error"] = result.stderr[:200] if result.stderr else "Unknown error"
                print(f"❌ {task['script']} failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            task["error_count"] += 1
            task["last_error"] = "Script timed out after 10 minutes"
            print(f"⏰ {task['script']} timed out")
            return False
        except Exception as e:
            task["error_count"] += 1
            task["last_error"] = str(e)[:200]
            print(f"💥 Error running {task['script']}: {e}")
            return False
        finally:
            # Restore original status (don't change continuous task status)
            task["status"] = original_status

# Global automation controller instance
automation_controller = AutomationController()

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print("\\n🛑 Received shutdown signal, stopping automation...")
    automation_controller.stop_all_tasks()
    # Don't call sys.exit() when used as a module
    if __name__ == "__main__":
        sys.exit(0)

# Only register signal handlers when run as main script
if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Crypto Dashboard Automation Controller")
    parser.add_argument("action", choices=["start", "stop", "status", "run"], 
                       help="Action to perform")
    parser.add_argument("--task", help="Specific task to control")
    
    args = parser.parse_args()
    
    if args.action == "start":
        if args.task:
            automation_controller.start_task(args.task)
        else:
            automation_controller.start_all_tasks()
            
        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            automation_controller.stop_all_tasks()
            
    elif args.action == "stop":
        if args.task:
            automation_controller.stop_task(args.task)
        else:
            automation_controller.stop_all_tasks()
            
    elif args.action == "status":
        status = automation_controller.get_status()
        print(json.dumps(status, indent=2))
        
    elif args.action == "run":
        if args.task:
            automation_controller.run_once(args.task)
        else:
            print("❌ Please specify a task to run with --task")