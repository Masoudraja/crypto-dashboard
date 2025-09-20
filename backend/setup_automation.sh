#!/usr/bin/env bash
"""
Crypto Dashboard Automation Setup Script
Automatically configures task scheduling based on your operating system
"""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

echo -e "${BLUE}🚀 Crypto Dashboard Automation Setup${NC}"
echo "=============================================="

# Check if virtual environment exists
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo "Please create a virtual environment first:"
    echo "  python -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Install schedule package if not already installed
echo -e "${YELLOW}📦 Installing required packages...${NC}"
source "$PROJECT_DIR/venv/bin/activate"
pip install schedule >> setup.log 2>&1

# Create logs directory
mkdir -p "$PROJECT_DIR/logs"
echo -e "${GREEN}✅ Created logs directory${NC}"

# Detect operating system
OS="$(uname -s)"
echo -e "${BLUE}🔍 Detected OS: $OS${NC}"

case "$OS" in
    Darwin*)
        echo -e "${YELLOW}🍎 Setting up macOS automation...${NC}"
        setup_macos_automation
        ;;
    Linux*)
        echo -e "${YELLOW}🐧 Setting up Linux automation...${NC}"
        setup_linux_automation
        ;;
    *)
        echo -e "${YELLOW}💻 Setting up generic Unix automation...${NC}"
        setup_generic_automation
        ;;
esac

setup_macos_automation() {
    echo "Choose macOS automation method:"
    echo "1. launchd (Recommended - Native macOS)"
    echo "2. crontab (Traditional Unix)"
    echo "3. Manual Python scheduler"
    
    read -p "Enter choice (1-3): " choice
    
    case $choice in
        1)
            setup_launchd
            ;;
        2)
            setup_crontab
            ;;
        3)
            setup_manual_scheduler
            ;;
        *)
            echo -e "${RED}Invalid choice. Setting up manual scheduler.${NC}"
            setup_manual_scheduler
            ;;
    esac
}

setup_launchd() {
    PLIST_FILE="$PROJECT_DIR/launchd/com.crypto-dashboard.scheduler.plist"
    LAUNCHD_DIR="$HOME/Library/LaunchAgents"
    
    # Update paths in plist file
    sed -i.bak "s|/Volumes/Masoud Case Sensetive/crypto-dashboard|$PROJECT_DIR|g" "$PLIST_FILE"
    
    # Create LaunchAgents directory if it doesn't exist
    mkdir -p "$LAUNCHD_DIR"
    
    # Copy plist file
    cp "$PLIST_FILE" "$LAUNCHD_DIR/"
    
    # Load the service
    launchctl load "$LAUNCHD_DIR/com.crypto-dashboard.scheduler.plist"
    
    echo -e "${GREEN}✅ launchd service configured and started${NC}"
    echo "Commands:"
    echo "  Start:  launchctl load ~/Library/LaunchAgents/com.crypto-dashboard.scheduler.plist"
    echo "  Stop:   launchctl unload ~/Library/LaunchAgents/com.crypto-dashboard.scheduler.plist"
    echo "  Status: launchctl list | grep crypto-dashboard"
}

setup_linux_automation() {
    if command -v systemctl &> /dev/null; then
        echo "Choose Linux automation method:"
        echo "1. systemd (Recommended for modern Linux)"
        echo "2. crontab (Traditional Unix)"
        echo "3. Manual Python scheduler"
        
        read -p "Enter choice (1-3): " choice
        
        case $choice in
            1)
                setup_systemd
                ;;
            2)
                setup_crontab
                ;;
            3)
                setup_manual_scheduler
                ;;
            *)
                echo -e "${RED}Invalid choice. Setting up crontab.${NC}"
                setup_crontab
                ;;
        esac
    else
        echo "systemd not available. Setting up crontab..."
        setup_crontab
    fi
}

setup_systemd() {
    SERVICE_FILE="$PROJECT_DIR/systemd/crypto-dashboard.service"
    
    # Update paths in service file
    sed -i.bak "s|/path/to/crypto-dashboard|$PROJECT_DIR|g" "$SERVICE_FILE"
    sed -i.bak "s|User=crypto-dashboard|User=$USER|g" "$SERVICE_FILE"
    sed -i.bak "s|Group=crypto-dashboard|Group=$(id -gn)|g" "$SERVICE_FILE"
    
    echo -e "${YELLOW}To complete systemd setup, run as root:${NC}"
    echo "  sudo cp $SERVICE_FILE /etc/systemd/system/"
    echo "  sudo systemctl daemon-reload"
    echo "  sudo systemctl enable crypto-dashboard.service"
    echo "  sudo systemctl start crypto-dashboard.service"
    echo ""
    echo "Commands:"
    echo "  Status: sudo systemctl status crypto-dashboard"
    echo "  Logs:   sudo journalctl -u crypto-dashboard -f"
    echo "  Stop:   sudo systemctl stop crypto-dashboard"
}

setup_crontab() {
    CRON_FILE="$PROJECT_DIR/crontab_config.txt"
    
    # Update project path in crontab file
    sed -i.bak "s|CRYPTO_DASHBOARD_PATH=.*|CRYPTO_DASHBOARD_PATH=$PROJECT_DIR|g" "$CRON_FILE"
    
    echo -e "${YELLOW}Setting up crontab...${NC}"
    echo "Current crontab will be backed up to crontab_backup.txt"
    
    # Backup current crontab
    crontab -l > crontab_backup.txt 2>/dev/null || echo "# No existing crontab" > crontab_backup.txt
    
    read -p "Install crontab now? (y/n): " install_cron
    
    if [[ $install_cron =~ ^[Yy]$ ]]; then
        # Install new crontab
        crontab "$CRON_FILE"
        echo -e "${GREEN}✅ Crontab installed${NC}"
        echo "Commands:"
        echo "  View:   crontab -l"
        echo "  Edit:   crontab -e"
        echo "  Remove: crontab -r"
    else
        echo -e "${YELLOW}Manual installation required:${NC}"
        echo "  crontab < $CRON_FILE"
    fi
}

setup_generic_automation() {
    setup_crontab
}

setup_manual_scheduler() {
    echo -e "${GREEN}✅ Manual scheduler setup${NC}"
    echo "To run the scheduler manually:"
    echo "  cd $PROJECT_DIR"
    echo "  source venv/bin/activate"
    echo "  python task_scheduler.py --daemon"
    echo ""
    echo "Available commands:"
    echo "  python task_scheduler.py --task price     # Run price collection"
    echo "  python task_scheduler.py --task news      # Run news fetch"
    echo "  python task_scheduler.py --task analysis  # Run analysis"
    echo "  python task_scheduler.py --task health    # Health check"
    echo "  python task_scheduler.py --daemon         # Run continuous scheduler"
}

# Test the scheduler
test_scheduler() {
    echo -e "${BLUE}🧪 Testing scheduler...${NC}"
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    echo "Running health check..."
    python task_scheduler.py --task health
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Scheduler test passed${NC}"
    else
        echo -e "${RED}❌ Scheduler test failed${NC}"
        echo "Check logs for details"
    fi
}

# Main execution
case "$OS" in
    Darwin*)
        setup_macos_automation
        ;;
    Linux*)
        setup_linux_automation
        ;;
    *)
        setup_generic_automation
        ;;
esac

echo ""
echo -e "${BLUE}🧪 Would you like to test the scheduler? (y/n)${NC}"
read -p "Test now: " test_now

if [[ $test_now =~ ^[Yy]$ ]]; then
    test_scheduler
fi

echo ""
echo -e "${GREEN}🎉 Automation setup complete!${NC}"
echo "Logs will be stored in: $PROJECT_DIR/logs/"
echo "Configuration files created:"
echo "  - task_scheduler.py (Main scheduler)"
echo "  - crontab_config.txt (Cron configuration)"
echo "  - systemd/crypto-dashboard.service (systemd service)"
echo "  - launchd/com.crypto-dashboard.scheduler.plist (macOS launchd)"
echo ""
echo "Next steps:"
echo "1. Verify your .env file has all required API keys"
echo "2. Test individual components: python main.py, python fetch_news.py"
echo "3. Monitor logs in the logs/ directory"
echo "4. Adjust schedule in task_scheduler.py if needed"