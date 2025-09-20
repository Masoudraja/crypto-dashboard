#!/bin/bash

# Crypto Dashboard Server Management Aliases
# Add these to your ~/.zshrc or ~/.bashrc for permanent access

# Navigate to project directory
alias cdcrypto='cd "/Volumes/Masoud Case Sensetive/crypto-dashboard"'

# Server management commands
alias crypto-start='cd "/Volumes/Masoud Case Sensetive/crypto-dashboard" && python server_manager.py start'
alias crypto-stop='cd "/Volumes/Masoud Case Sensetive/crypto-dashboard" && python server_manager.py stop'
alias crypto-restart='cd "/Volumes/Masoud Case Sensetive/crypto-dashboard" && python server_manager.py restart'
alias crypto-status='cd "/Volumes/Masoud Case Sensetive/crypto-dashboard" && python server_manager.py status'

# Background server management
alias crypto-start-bg='cd "/Volumes/Masoud Case Sensetive/crypto-dashboard" && python server_manager.py start --background'
alias crypto-restart-bg='cd "/Volumes/Masoud Case Sensetive/crypto-dashboard" && python server_manager.py restart --background'

# Alternative port management
alias crypto-start-8001='cd "/Volumes/Masoud Case Sensetive/crypto-dashboard" && python server_manager.py --port 8001 start'

echo "Crypto Dashboard Server Management Commands:"
echo "  crypto-start      - Start server in foreground"
echo "  crypto-stop       - Stop all servers"
echo "  crypto-restart    - Restart server"
echo "  crypto-status     - Show server status"
echo "  crypto-start-bg   - Start server in background"
echo "  crypto-restart-bg - Restart server in background"
echo "  cdcrypto          - Navigate to project directory"
echo ""
echo "To make these aliases permanent, add the following to your ~/.zshrc:"
echo ""
echo "# Crypto Dashboard Aliases"
echo "source '/Volumes/Masoud Case Sensetive/crypto-dashboard/crypto_aliases.sh'"