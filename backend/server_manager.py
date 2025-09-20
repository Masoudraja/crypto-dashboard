#!/usr/bin/env python3
"""
Crypto Dashboard Server Manager
A comprehensive script to manage FastAPI server lifecycle and prevent port conflicts.
"""

import os
import sys
import signal
import subprocess
import psutil
import time
import argparse
from typing import List, Optional

class ServerManager:
    def __init__(self, port: int = 8000, host: str = "127.0.0.1"):
        self.port = port
        self.host = host
        self.project_dir = "/Volumes/Masoud Case Sensetive/crypto-dashboard"
        
    def find_processes_on_port(self) -> List[dict]:
        """Find all processes using the specified port."""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                for conn in proc.connections():
                    if conn.laddr.port == self.port:
                        processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cmdline': ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return processes
    
    def find_uvicorn_processes(self) -> List[dict]:
        """Find all uvicorn processes."""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if 'uvicorn' in cmdline and 'crypto-dashboard' in cmdline:
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmdline': cmdline
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return processes
    
    def kill_process(self, pid: int) -> bool:
        """Safely kill a process."""
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            proc.wait(timeout=5)
            print(f"✅ Successfully terminated process {pid}")
            return True
        except psutil.TimeoutExpired:
            try:
                proc.kill()
                print(f"⚠️  Force killed process {pid}")
                return True
            except:
                print(f"❌ Failed to kill process {pid}")
                return False
        except psutil.NoSuchProcess:
            print(f"ℹ️  Process {pid} not found (already terminated)")
            return True
        except Exception as e:
            print(f"❌ Error killing process {pid}: {e}")
            return False
    
    def stop_all_servers(self) -> bool:
        """Stop all crypto-dashboard related servers."""
        print("🛑 Stopping all crypto-dashboard servers...")
        
        # Find and stop processes on our port
        port_processes = self.find_processes_on_port()
        if port_processes:
            print(f"Found {len(port_processes)} process(es) on port {self.port}:")
            for proc in port_processes:
                print(f"  - PID {proc['pid']}: {proc['name']} - {proc['cmdline']}")
                self.kill_process(proc['pid'])
        
        # Find and stop all uvicorn processes
        uvicorn_processes = self.find_uvicorn_processes()
        if uvicorn_processes:
            print(f"Found {len(uvicorn_processes)} uvicorn process(es):")
            for proc in uvicorn_processes:
                print(f"  - PID {proc['pid']}: {proc['cmdline']}")
                self.kill_process(proc['pid'])
        
        # Wait a moment for processes to clean up
        time.sleep(2)
        
        # Verify port is free
        remaining_processes = self.find_processes_on_port()
        if remaining_processes:
            print(f"⚠️  Warning: {len(remaining_processes)} process(es) still using port {self.port}")
            return False
        else:
            print(f"✅ Port {self.port} is now free")
            return True
    
    def start_server(self, background: bool = False) -> bool:
        """Start the FastAPI server."""
        print(f"🚀 Starting server on {self.host}:{self.port}...")
        
        # Change to project directory
        os.chdir(self.project_dir)
        
        # Prepare command
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "api:app", 
            "--reload", 
            "--host", self.host,
            "--port", str(self.port)
        ]
        
        try:
            if background:
                # Start in background
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE
                )
                print(f"✅ Server started in background (PID: {process.pid})")
                print(f"🌐 API available at: http://{self.host}:{self.port}")
                print(f"📖 API docs at: http://{self.host}:{self.port}/docs")
                return True
            else:
                # Start in foreground
                print(f"🌐 API will be available at: http://{self.host}:{self.port}")
                print(f"📖 API docs at: http://{self.host}:{self.port}/docs")
                print("Press Ctrl+C to stop the server")
                subprocess.run(cmd, check=True)
                return True
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to start server: {e}")
            return False
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
            return True
    
    def restart_server(self, background: bool = False) -> bool:
        """Stop and restart the server."""
        print("🔄 Restarting server...")
        self.stop_all_servers()
        time.sleep(1)
        return self.start_server(background)
    
    def status(self) -> None:
        """Show server status."""
        print("📊 Server Status:")
        print(f"Target port: {self.port}")
        print(f"Target host: {self.host}")
        print()
        
        # Check port usage
        port_processes = self.find_processes_on_port()
        if port_processes:
            print(f"🔴 Port {self.port} is in use:")
            for proc in port_processes:
                print(f"  - PID {proc['pid']}: {proc['name']}")
                print(f"    Command: {proc['cmdline']}")
        else:
            print(f"🟢 Port {self.port} is free")
        
        print()
        
        # Check uvicorn processes
        uvicorn_processes = self.find_uvicorn_processes()
        if uvicorn_processes:
            print(f"📋 Found {len(uvicorn_processes)} uvicorn process(es):")
            for proc in uvicorn_processes:
                print(f"  - PID {proc['pid']}: {proc['cmdline']}")
        else:
            print("📋 No crypto-dashboard uvicorn processes found")


def main():
    parser = argparse.ArgumentParser(description="Crypto Dashboard Server Manager")
    parser.add_argument("--port", type=int, default=8000, help="Port to use (default: 8000)")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start the server")
    start_parser.add_argument("--background", "-b", action="store_true", help="Start in background")
    
    # Stop command
    subparsers.add_parser("stop", help="Stop all servers")
    
    # Restart command
    restart_parser = subparsers.add_parser("restart", help="Restart the server")
    restart_parser.add_argument("--background", "-b", action="store_true", help="Start in background")
    
    # Status command
    subparsers.add_parser("status", help="Show server status")
    
    args = parser.parse_args()
    
    manager = ServerManager(port=args.port, host=args.host)
    
    if args.command == "start":
        manager.start_server(background=args.background)
    elif args.command == "stop":
        manager.stop_all_servers()
    elif args.command == "restart":
        manager.restart_server(background=args.background)
    elif args.command == "status":
        manager.status()
    else:
        # Default: restart server
        manager.restart_server()


if __name__ == "__main__":
    main()