# Setup Guide - Algorithmic Trading Tool

This guide will help you set up and configure the Algorithmic Trading Tool for the first time.

## Prerequisites

Before you begin, ensure you have:
- Python 3.8 or higher installed
- A broker account (Angel One or Dhan) with API access
- Basic understanding of trading concepts
- Familiarity with command line/terminal

## Step 1: System Setup

### Linux/Ubuntu
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install Redis (optional but recommended)
sudo apt install redis-server -y
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Install TA-Lib dependencies
sudo apt-get install build-essential
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
cd ..
```

### macOS
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python

# Install Redis
brew install redis
brew services start redis

# Install TA-Lib
brew install ta-lib
```

### Windows
1. Download Python from python.org (3.8+)
2. Install Redis for Windows from GitHub releases
3. Install TA-Lib:
   - Download TA-Lib whl file from https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
   - Install using: `pip install TA_Lib-0.4.24-cp39-cp39-win_amd64.whl` (adjust version)

## Step 2: Download and Setup

1. **Download the Tool**
   ```bash
   # If you have the files, navigate to the directory
   cd /path/to/algo_trading_tool
   
   # Make the run script executable
   chmod +x run.sh
   ```

2. **Install Dependencies**
   ```bash
   # Use the automated setup script
   ./run.sh
   
   # OR manually:
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Step 3: Broker Configuration

### Angel One Setup

1. **Create Account**
   - Visit [Angel One](https://angelone.in)
   - Create a trading account
   - Complete KYC verification

2. **Enable API Access**
   - Login to your Angel One account
   - Go to Profile → API
   - Apply for API access
   - Wait for approval (usually 1-2 business days)

3. **Get API Credentials**
   After approval, you'll receive:
   - Client ID
   - Password
   - API Key
   - Secret Key

### Dhan Setup

1. **Create Account**
   - Visit [Dhan](https://dhan.co)
   - Create a trading account
   - Complete KYC verification

2. **Generate API Token**
   - Login to Dhan web platform
   - Go to Settings → API
   - Generate API access token
   - Note down Client ID and Access Token

## Step 4: Configuration

1. **Copy Environment Template**
   ```bash
   cp .env.example .env
   ```

2. **Edit Configuration**
   Open `.env` file and add your credentials:
   
   ```env
   # Application Settings
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   
   # Angel One Broker API
   ANGEL_ONE_CLIENT_ID=YOUR_CLIENT_ID
   ANGEL_ONE_PASSWORD=YOUR_PASSWORD
   ANGEL_ONE_API_KEY=YOUR_API_KEY
   ANGEL_ONE_SECRET_KEY=YOUR_SECRET_KEY
   
   # Dhan Broker API
   DHAN_CLIENT_ID=YOUR_CLIENT_ID
   DHAN_ACCESS_TOKEN=YOUR_ACCESS_TOKEN
   
   # Trading Configuration
   DEFAULT_CAPITAL=100000
   MAX_RISK_PER_TRADE=0.02
   MAX_PORTFOLIO_RISK=0.06
   DEFAULT_STOP_LOSS=0.02
   DEFAULT_TARGET=0.04
   ```

## Step 5: Real-time Data Configuration (Optional)

For better performance, set up real-time data sources:

### Alpha Vantage (Free Tier Available)
1. Sign up at [alphavantage.co](https://www.alphavantage.co)
2. Get free API key (500 requests/day)
3. Add to `.env`: `ALPHA_VANTAGE_API_KEY=your_key`

### Twelve Data (Free Tier Available)
1. Sign up at [twelvedata.com](https://twelvedata.com)
2. Get free API key (800 requests/day)
3. Add to `.env`: `TWELVEDATA_API_KEY=your_key`

### Polygon.io (Paid)
1. Sign up at [polygon.io](https://polygon.io)
2. Choose a paid plan
3. Add to `.env`: `POLYGON_API_KEY=your_key`

## Step 6: First Run

1. **Start the Application**
   ```bash
   ./run.sh
   ```
   
   OR manually:
   ```bash
   source venv/bin/activate
   python app.py
   ```

2. **Access Dashboard**
   - Open browser and go to: http://localhost:5000
   - You should see the trading dashboard

3. **Initial Configuration**
   - Click on "Settings" in the navigation
   - Configure risk parameters
   - Enable "Paper Trading Mode" for testing
   - Save settings

## Step 7: Testing and Validation

### Paper Trading Test
1. **Enable Paper Trading**
   - Go to Settings
   - Enable "Paper Trading Mode"
   - This allows testing without real money

2. **Configure Strategies**
   - Enable/disable strategies as desired
   - Start with conservative settings

3. **Run Backtest**
   - Navigate to "Backtesting" section
   - Select NIFTY or BANKNIFTY
   - Choose last month's date range
   - Run backtest to validate system

4. **Start Paper Trading**
   - Select symbols to trade
   - Enable desired strategies
   - Click "Start Trading"
   - Monitor for any errors

### Broker Connection Test
1. **Check Broker Status**
   - Go to Settings
   - Verify broker shows "Connected" status
   - If failed, check API credentials

2. **Test Market Data**
   - Check if live prices are updating
   - Verify data source is working

## Step 8: Going Live (When Ready)

⚠️ **Important**: Only proceed after thorough testing

1. **Final Checks**
   - Backtest shows positive results
   - Paper trading works correctly
   - All systems stable for at least a week

2. **Enable Live Trading**
   - Go to Settings
   - Disable "Paper Trading Mode"
   - Enable "Auto Trading (Live)"
   - Set conservative risk parameters

3. **Start with Small Capital**
   - Begin with small amounts
   - Gradually increase as confidence builds
   - Monitor closely

## Troubleshooting

### Common Issues and Solutions

1. **Import Error: No module named 'talib'**
   ```bash
   # Install TA-Lib dependencies first (see Step 1)
   pip install TA-Lib
   ```

2. **Redis Connection Error**
   ```bash
   # Install and start Redis
   sudo apt install redis-server  # Linux
   brew install redis            # macOS
   sudo systemctl start redis-server
   ```

3. **Broker API Error**
   - Verify API credentials in `.env`
   - Check if API access is enabled in broker account
   - Ensure correct API endpoints

4. **Data Source Error**
   - Check API keys in `.env`
   - Verify rate limits not exceeded
   - Check internet connection

5. **Permission Denied on run.sh**
   ```bash
   chmod +x run.sh
   ```

### Log Files
- Application logs: `logs/trading.log`
- Error logs: Check terminal output
- Set debug mode: `DEBUG=True` in `.env`

## Security Best Practices

1. **API Key Security**
   - Never share your `.env` file
   - Use different API keys for testing/production
   - Regularly rotate API keys

2. **Trading Security**
   - Always start with paper trading
   - Set appropriate risk limits
   - Monitor positions actively
   - Have emergency stop procedures

3. **System Security**
   - Keep system updated
   - Use secure networks
   - Regular backups of configurations

## Performance Optimization

1. **System Resources**
   - Ensure adequate RAM (4GB+ recommended)
   - Good internet connection
   - SSD storage preferred

2. **Configuration**
   - Use Redis for caching
   - Optimize risk parameters
   - Fine-tune strategy settings

## Next Steps

After successful setup:
1. Run extensive backtests
2. Paper trade for at least 1-2 weeks
3. Study strategy performance
4. Gradually increase capital allocation
5. Monitor and refine continuously

## Support

If you encounter issues:
1. Check this guide
2. Review log files
3. Verify all prerequisites are met
4. Test with minimal configuration first

Remember: Trading involves risk. Always test thoroughly and start conservatively.