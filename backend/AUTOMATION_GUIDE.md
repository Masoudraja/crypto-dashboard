# 🤖 Crypto Dashboard Automation Guide

## Overview

Your crypto dashboard now includes a comprehensive automation system that keeps your data fresh automatically. The system supports multiple scheduling methods and provides robust error handling, logging, and monitoring.

## 📋 Automation Schedule

| **Task** | **Frequency** | **Purpose** |
|----------|---------------|-------------|
| 📊 **Price Data Collection** | Every 5 minutes | Fetch latest prices + 15+ technical indicators |
| 📰 **News Aggregation** | Every 30 minutes | Collect news from 7+ sources |
| 📈 **Market Analysis** | Every hour | Run correlation, volatility, momentum analysis |
| 🏥 **Health Check** | Every 4 hours | Verify database and system health |
| 🧹 **Daily Maintenance** | Daily at 1 AM | Clean logs, optimize database |
| 🔄 **Full Backfill** | Sundays at 2 AM | Complete historical data refresh |

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)
```bash
cd /path/to/crypto-dashboard
./setup_automation.sh
```

### Option 2: Manual Setup

#### For macOS (launchd - Native):
```bash
# Copy plist file
cp launchd/com.crypto-dashboard.scheduler.plist ~/Library/LaunchAgents/

# Load the service
launchctl load ~/Library/LaunchAgents/com.crypto-dashboard.scheduler.plist

# Check status
launchctl list | grep crypto-dashboard
```

#### For Linux (systemd):
```bash
# Copy service file (as root)
sudo cp systemd/crypto-dashboard.service /etc/systemd/system/

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable crypto-dashboard.service
sudo systemctl start crypto-dashboard.service

# Check status
sudo systemctl status crypto-dashboard
```

#### For Any Unix System (crontab):
```bash
# Install crontab
crontab < crontab_config.txt

# Verify installation
crontab -l
```

#### Manual Python Scheduler:
```bash
# Run continuously in background
nohup python task_scheduler.py --daemon > logs/scheduler.log 2>&1 &

# Or run in screen/tmux session
screen -S crypto-scheduler
python task_scheduler.py --daemon
# Ctrl+A, D to detach
```

## 🎯 Manual Task Execution

Run individual tasks manually:

```bash
# Health check
python task_scheduler.py --task health

# Collect price data
python task_scheduler.py --task price

# Fetch news
python task_scheduler.py --task news

# Run market analysis
python task_scheduler.py --task analysis

# Full historical backfill
python task_scheduler.py --task backfill

# Daily maintenance
python task_scheduler.py --task maintenance
```

## 📊 Monitoring & Logs

### Log Files Location: `logs/`
- `scheduler.log` - Main scheduler activity
- `price_collection.log` - Price data collection
- `news_fetch.log` - News aggregation
- `analysis.log` - Market analysis
- `health_check.log` - System health
- `maintenance.log` - Daily maintenance
- `backfill.log` - Historical data backfill

### Real-time Monitoring:
```bash
# Watch scheduler logs
tail -f logs/scheduler.log

# Watch all logs
tail -f logs/*.log

# macOS launchd logs
log stream --predicate 'process == "python"' --info

# Linux systemd logs
sudo journalctl -u crypto-dashboard -f
```

## 🔧 Configuration

### Customize Schedule
Edit `task_scheduler.py` to modify frequencies:

```python
# Current schedule
schedule.every(5).minutes.do(self.collect_price_data)     # Price data
schedule.every(30).minutes.do(self.fetch_news)           # News
schedule.every().hour.do(self.update_analysis)           # Analysis

# Example customizations
schedule.every(2).minutes.do(self.collect_price_data)     # More frequent
schedule.every(15).minutes.do(self.fetch_news)           # More frequent news
schedule.every(2).hours.do(self.update_analysis)         # Less frequent analysis
```

### Environment Variables
Ensure your `.env` file contains:
```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=crypto_dashboard
DB_USER=your_user
DB_PASSWORD=your_password

# APIs
COINGECKO_API_KEY=your_coingecko_key
COINMARKETCAP_API_KEY=your_cmc_key
CRYPTOCOMPARE_API_KEY=your_cc_key
NEWS_API_KEY=your_news_key
CRYPTOPANIC_API_KEY=your_cp_key
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Permission Denied
```bash
# Make scripts executable
chmod +x setup_automation.sh
chmod +x task_scheduler.py
```

#### 2. Virtual Environment Not Found
```bash
# Ensure virtual environment exists
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. Database Connection Failed
```bash
# Test database connection
python -c "from config import *; import psycopg2; psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)"
```

#### 4. Import Errors
```bash
# Install missing dependencies
pip install -r requirements.txt
```

### Service Management

#### macOS launchd:
```bash
# Start service
launchctl load ~/Library/LaunchAgents/com.crypto-dashboard.scheduler.plist

# Stop service
launchctl unload ~/Library/LaunchAgents/com.crypto-dashboard.scheduler.plist

# Remove service
rm ~/Library/LaunchAgents/com.crypto-dashboard.scheduler.plist
```

#### Linux systemd:
```bash
# Start/stop service
sudo systemctl start crypto-dashboard
sudo systemctl stop crypto-dashboard

# Enable/disable auto-start
sudo systemctl enable crypto-dashboard
sudo systemctl disable crypto-dashboard

# Remove service
sudo systemctl stop crypto-dashboard
sudo systemctl disable crypto-dashboard
sudo rm /etc/systemd/system/crypto-dashboard.service
sudo systemctl daemon-reload
```

#### Crontab:
```bash
# Remove all cron jobs
crontab -r

# Edit cron jobs
crontab -e

# Restore from backup
crontab < crontab_backup.txt
```

## 🎯 Performance Optimization

### Resource Usage
- **CPU**: Low to moderate during data collection
- **Memory**: ~100-500 MB depending on coin count
- **Network**: API calls every few minutes
- **Disk**: Log files grow over time (auto-cleaned weekly)

### Scaling Tips
1. **Increase coin count**: Edit `COINS_TO_TRACK` in `config.py`
2. **Add more news sources**: Update `RSS_FEEDS` in `fetch_news.py`
3. **Adjust frequencies**: Modify schedule in `task_scheduler.py`
4. **Database optimization**: Run `VACUUM` and `ANALYZE` periodically

## 🛡️ Security Considerations

1. **API Keys**: Store in `.env` file, never commit to git
2. **Database**: Use dedicated user with minimal permissions
3. **Logs**: Contain no sensitive data, safe to backup
4. **Network**: Consider firewall rules for database access

## 📈 Advanced Features

### Custom Alerts (Future Enhancement)
```python
# Add to task_scheduler.py
def check_price_alerts(self):
    # Check for significant price movements
    # Send notifications via email/Slack/Discord
    pass
```

### API Integration (Future Enhancement)
```python
# Add to api.py
@app.get("/scheduler/status")
def get_scheduler_status():
    # Return scheduler status and last run times
    pass
```

## 🎉 Success Indicators

Your automation is working correctly when you see:
- ✅ Regular log entries every few minutes
- ✅ Fresh data in your database
- ✅ No error messages in health checks
- ✅ API returning recent data
- ✅ News articles being updated

## 📞 Support

If you encounter issues:
1. Check the logs in `logs/` directory
2. Run manual health check: `python task_scheduler.py --task health`
3. Verify individual components work: `python main.py`, `python fetch_news.py`
4. Check database connectivity and API keys

Your crypto dashboard is now fully automated! 🚀