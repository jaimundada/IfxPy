# Algorithmic Trading Tool

A comprehensive algorithmic trading system for Indian stock markets with support for index and options trading, real-time data processing, intelligent strategy management, and broker API integration.

## Features

### Core Features
- **Multi-Strategy Trading**: Momentum, Mean Reversion, Volatility, and Options strategies
- **Intelligent Options Trading**: Automatic strike selection and risk management for options
- **Broker Integration**: Angel One and Dhan API support for live trading
- **Real-time Data**: Support for multiple data sources (Yahoo Finance, Alpha Vantage, Polygon, Twelve Data)
- **Comprehensive Backtesting**: Minute-by-minute historical simulation
- **Risk Management**: Advanced position sizing, stop-loss, and portfolio risk controls
- **Modern Web Interface**: Real-time dashboard with charts and trading controls

### Advanced Features
- **Automatic Strike Selection**: AI-powered options strike selection based on market conditions
- **Risk-Reward Optimization**: Intelligent position sizing based on confidence and risk parameters
- **Multi-timeframe Analysis**: Supports 1m, 5m, 15m, 1h, and daily data
- **Real-time Monitoring**: Live P&L tracking, position monitoring, and alert system
- **Paper Trading**: Safe testing environment before going live
- **Performance Analytics**: Detailed backtesting results with key metrics

## Architecture

```
algo_trading_tool/
├── src/
│   ├── data_sources/        # Data fetching and management
│   ├── strategies/          # Trading strategies and signal generation
│   ├── brokers/            # Broker API integrations
│   ├── backtesting/        # Backtesting engine
│   ├── risk_management/    # Risk management system
│   └── utils/              # Utility functions and logging
├── templates/              # Web interface templates
├── static/                 # CSS, JavaScript, and assets
├── config/                 # Configuration files
├── logs/                   # Application logs
└── tests/                  # Unit tests
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Redis (optional, for caching)

### Setup Steps

1. **Clone or download the repository**
   ```bash
   cd /workspace/algo_trading_tool
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` file with your API keys and configuration.

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the dashboard**
   Open your browser and go to `http://localhost:5000`

## Configuration

### Environment Variables

Create a `.env` file with the following configuration:

```env
# Broker API Keys
ANGEL_ONE_CLIENT_ID=your_client_id
ANGEL_ONE_PASSWORD=your_password
ANGEL_ONE_API_KEY=your_api_key
ANGEL_ONE_SECRET_KEY=your_secret_key

DHAN_CLIENT_ID=your_client_id
DHAN_ACCESS_TOKEN=your_access_token

# Real-time Data Sources (Optional)
ALPHA_VANTAGE_API_KEY=your_key
POLYGON_API_KEY=your_key
TWELVEDATA_API_KEY=your_key

# Trading Configuration
DEFAULT_CAPITAL=100000
MAX_RISK_PER_TRADE=0.02
MAX_PORTFOLIO_RISK=0.06
DEFAULT_STOP_LOSS=0.02
DEFAULT_TARGET=0.04
```

### Broker Setup

#### Angel One (Angel Broking)
1. Create an account at Angel One
2. Apply for API access
3. Get your Client ID, Password, API Key, and Secret Key
4. Add these to your `.env` file

#### Dhan
1. Create an account at Dhan
2. Generate API access token
3. Add Client ID and Access Token to your `.env` file

### Data Source Setup

For **FREE delayed data** (default):
- Yahoo Finance is used automatically (15-minute delay)

For **REAL-TIME data** (paid services):
- **Alpha Vantage**: Get free/paid API key from alphavantage.co
- **Polygon.io**: Get API key from polygon.io (real-time US data)
- **Twelve Data**: Get API key from twelvedata.com

## Usage

### Getting Started

1. **Paper Trading Mode** (Recommended for beginners)
   - Enable "Paper Trading Mode" in settings
   - Test strategies without real money
   - Monitor performance and refine settings

2. **Configure Strategies**
   - Enable/disable strategies in the dashboard
   - Adjust risk parameters in settings
   - Set stop-loss and target percentages

3. **Start Trading**
   - Select symbols to trade (NIFTY, BANKNIFTY, FINNIFTY)
   - Choose active strategies
   - Click "Start Trading"

### Backtesting

1. **Navigate to Backtesting Section**
   - Click "Backtesting" in the navigation

2. **Configure Backtest**
   - Select symbol (NIFTY, BANKNIFTY, FINNIFTY)
   - Choose date range
   - Set initial capital
   - Select strategy to test

3. **Run Backtest**
   - Click "Run Backtest"
   - Wait for completion
   - Analyze results and metrics

### Strategy Configuration

#### Momentum Strategy
- Trades based on trend direction
- Uses moving averages and RSI
- Best for trending markets

#### Mean Reversion Strategy
- Trades against short-term moves
- Uses Bollinger Bands and RSI
- Best for range-bound markets

#### Volatility Strategy
- Trades breakouts with volume confirmation
- Uses volatility and volume indicators
- Best for high-volatility periods

#### Options Strategies
- **Options Selling**: Premium collection strategies (strangles, iron condors)
- **Options Buying**: Directional trades with automatic strike selection

## Real-time Data Sources

### Free Sources (Delayed)
- **Yahoo Finance**: 15-minute delayed data (free)

### Paid Sources (Real-time)
- **Alpha Vantage**: Real-time US data, some Indian indices
- **Polygon.io**: Real-time US market data
- **Twelve Data**: Global real-time data including Indian markets

### Setup Instructions for Paid Sources

1. **Alpha Vantage**
   - Sign up at alphavantage.co
   - Get your free API key (500 requests/day)
   - Or upgrade to paid plan for more requests
   - Add key to `.env`: `ALPHA_VANTAGE_API_KEY=your_key`

2. **Polygon.io**
   - Sign up at polygon.io
   - Choose a paid plan
   - Get your API key
   - Add key to `.env`: `POLYGON_API_KEY=your_key`

3. **Twelve Data**
   - Sign up at twelvedata.com
   - Choose free tier (800 requests/day) or paid plan
   - Get your API key
   - Add key to `.env`: `TWELVEDATA_API_KEY=your_key`

## Risk Management

### Position Sizing
- **Fixed Amount**: Fixed amount per trade
- **Percentage**: Percentage of capital per trade
- **Risk-based**: Based on stop-loss and risk tolerance

### Risk Controls
- Maximum risk per trade (default: 2%)
- Maximum portfolio risk (default: 6%)
- Position concentration limits
- Daily loss limits
- Correlation risk management

### Stop-Loss and Targets
- Automatic stop-loss execution
- Trailing stop-loss support
- Target-based exits
- Time-based exits

## Troubleshooting

### Common Issues

1. **"No module named 'talib'"**
   ```bash
   # Install TA-Lib dependencies
   sudo apt-get install libta-lib-dev  # Linux
   brew install ta-lib                 # macOS
   pip install TA-Lib
   ```

2. **Broker API Connection Failed**
   - Verify your API credentials in `.env`
   - Check if your broker account has API access enabled
   - Ensure you're using the correct API endpoints

3. **Data Source Not Working**
   - Check your API keys in `.env`
   - Verify API rate limits
   - Check internet connection

4. **Redis Connection Error**
   - Install Redis: `sudo apt-get install redis-server`
   - Start Redis: `sudo service redis-server start`
   - Or disable Redis in config (will use in-memory cache)

### Logging
- Application logs are stored in `logs/trading.log`
- Set log level in `.env`: `LOG_LEVEL=DEBUG|INFO|WARNING|ERROR`

## API Endpoints

### Trading Control
- `POST /api/start_trading` - Start automated trading
- `POST /api/stop_trading` - Stop automated trading
- `GET /api/positions` - Get current positions
- `GET /api/market_data/<symbol>` - Get market data

### Backtesting
- `POST /api/backtest` - Run backtest simulation

### WebSocket Events
- `trade_executed` - New trade execution
- `position_closed` - Position closed
- `trading_error` - Trading error occurred
- `market_update` - Real-time market updates

## Development

### Adding New Strategies
1. Create strategy class in `src/strategies/`
2. Implement `generate_signals()` method
3. Add strategy to `StrategyManager`
4. Update web interface

### Adding New Brokers
1. Create broker class in `src/brokers/`
2. Implement required methods
3. Add to `BrokerManager`
4. Update configuration

### Running Tests
```bash
python -m pytest tests/
```

## Security Considerations

### API Key Security
- Never commit API keys to version control
- Use environment variables for sensitive data
- Rotate API keys regularly
- Use separate API keys for testing and production

### Trading Safety
- Always start with paper trading
- Test strategies thoroughly before going live
- Set appropriate risk limits
- Monitor positions actively
- Have emergency stop procedures

## Performance Optimization

### For Better Performance
- Use Redis for caching market data
- Optimize database queries
- Use real-time data sources for better signals
- Fine-tune strategy parameters
- Monitor system resources

### Scaling
- Use multiple instances for different symbols
- Implement distributed backtesting
- Use database for position storage
- Add monitoring and alerting

## License

This project is for educational and personal use. Please ensure compliance with:
- Broker API terms of service
- Data provider terms of service
- Local financial regulations
- Securities trading laws

## Disclaimer

⚠️ **Important**: This software is for educational purposes only. Trading involves substantial risk and is not suitable for all investors. Past performance does not guarantee future results. Always:

- Test thoroughly in paper trading mode
- Start with small amounts
- Understand the risks involved
- Consult with financial advisors
- Comply with local regulations

The developers are not responsible for any trading losses or damages resulting from the use of this software.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review logs in `logs/trading.log`
3. Ensure all dependencies are installed correctly
4. Verify API credentials and configurations

## Roadmap

Future enhancements planned:
- [ ] Machine learning-based strategies
- [ ] Additional broker integrations
- [ ] Mobile app interface
- [ ] Advanced options Greeks analysis
- [ ] Portfolio optimization algorithms
- [ ] Social trading features
- [ ] Advanced backtesting metrics
- [ ] Real-time news sentiment analysis