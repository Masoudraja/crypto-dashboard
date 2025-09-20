#!/usr/bin/env python3
"""
Start Enhanced Crypto Dashboard Server
Automatically handles port conflicts and starts the server
"""

import subprocess
import sys
import time

def kill_port_conflicts():
    """Kill any processes using port 8000"""
    try:
        # Find processes using port 8000
        result = subprocess.run(['lsof', '-i', ':8000'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            print("🔍 Found processes using port 8000, terminating...")
            
            # Extract PIDs and kill them
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            pids = []
            for line in lines:
                parts = line.split()
                if len(parts) > 1:
                    pids.append(parts[1])
            
            if pids:
                subprocess.run(['kill', '-9'] + pids)
                print(f"✅ Terminated processes: {', '.join(pids)}")
                time.sleep(1)
        else:
            print("✅ Port 8000 is free")
    except Exception as e:
        print(f"⚠️  Error checking port: {e}")

def start_server():
    """Start the enhanced crypto dashboard server"""
    print("🚀 Starting Enhanced Crypto Dashboard Server...")
    try:
        subprocess.run(['uvicorn', 'api:app', '--reload'], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Enhanced Crypto Dashboard - Smart Server Starter")
    print("=" * 50)
    
    # Handle port conflicts
    kill_port_conflicts()
    
    # Start server
    start_server()