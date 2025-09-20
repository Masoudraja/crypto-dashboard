# Crypto Dashboard Server Management Guide

## 🛠️ **Permanent Solution for Port Conflicts**

This guide provides a **permanent solution** to avoid port conflicts and manage your crypto dashboard server efficiently.

## 📋 **Available Commands**

### **Basic Server Management**

```bash
# Navigate to project directory
cd "/Volumes/Masoud Case Sensetive/crypto-dashboard"

# Start server (foreground - recommended for development)
python server_manager.py start

# Start server in background (for production-like usage)
python server_manager.py start --background

# Stop all servers (cleans up port conflicts)
python server_manager.py stop

# Restart server (stops all, then starts fresh)
python server_manager.py restart

# Check server status and port usage
python server_manager.py status
```

### **Alternative Port Usage**

```bash
# Use different port if needed
python server_manager.py --port 8001 start
python server_manager.py --port 8001 restart
```

## 🔧 **Setting Up Permanent Aliases (Optional)**

Add these to your `~/.zshrc` for easy access:

```bash
# Add this line to ~/.zshrc
source '/Volumes/Masoud Case Sensetive/crypto-dashboard/crypto_aliases.sh'
```

Then reload your shell:

```bash
source ~/.zshrc
```

After setup, you can use these short commands:

```bash
crypto-start      # Start server
crypto-stop       # Stop all servers
crypto-restart    # Restart server
crypto-status     # Show status
crypto-start-bg   # Start in background
cdcrypto          # Navigate to project
```

## 🚀 **How It Solves Port Conflicts**

### **The Problem:**

- Multiple uvicorn processes running on the same port
- Old processes not properly terminated
- Manual `kill -9` commands needed

### **The Solution:**

1. **Smart Process Detection**: Automatically finds all processes using port 8000
2. **Safe Termination**: Gracefully stops processes with timeout fallback
3. **Complete Cleanup**: Removes both main and child processes
4. **Verification**: Confirms port is free before starting new server
5. **Background Options**: Supports both foreground and background modes

## 📊 **Features**

- ✅ **Automatic Conflict Resolution**: No more manual `kill -9` commands
- ✅ **Cross-Platform**: Works on macOS, Linux, and Windows
- ✅ **Safe Process Management**: Graceful termination with force fallback
- ✅ **Status Monitoring**: Real-time port and process status
- ✅ **Background Mode**: Run server without blocking terminal
- ✅ **Multiple Port Support**: Easy port switching when needed
- ✅ **Enhanced Logging**: Clear feedback on all operations

## 🎯 **Usage Examples**

### **Development Workflow:**

```bash
# Start developing
cd "/Volumes/Masoud Case Sensetive/crypto-dashboard"
python server_manager.py start

# When done, stop cleanly
python server_manager.py stop
```

### **Production-like Setup:**

```bash
# Start in background
python server_manager.py start --background

# Check if running
python server_manager.py status

# Restart if needed
python server_manager.py restart --background
```

### **Troubleshooting:**

```bash
# Check what's using the port
python server_manager.py status

# Force clean restart
python server_manager.py stop
python server_manager.py start
```

## 🔧 **Advanced Configuration**

The server manager supports these options:

- `--port`: Change port (default: 8000)
- `--host`: Change host (default: 127.0.0.1)
- `--background`: Run in background mode

## 🎉 **Benefits**

1. **No More Port Conflicts**: Automatically handles all conflicts
2. **One Command Solution**: `python server_manager.py restart` fixes everything
3. **Production Ready**: Background mode for deployment
4. **Developer Friendly**: Clear status and error messages
5. **Time Saving**: No more manual process hunting

## 🚨 **Never Again Commands**

You'll **never need these manual commands again**:

```bash
# ❌ Old way (manual and error-prone)
lsof -i :8000
kill -9 <PID>
uvicorn api:app --reload

# ✅ New way (automatic and reliable)
python server_manager.py restart
```

## 🎯 **Your New Workflow**

**Every time you want to start the server:**

```bash
cd "/Volumes/Masoud Case Sensetive/crypto-dashboard"
python server_manager.py restart
```

**That's it!** No more port conflicts, no more manual process management, no more frustration! 🎉
