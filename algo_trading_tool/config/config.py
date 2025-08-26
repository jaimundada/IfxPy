import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Main configuration class for the algorithmic trading tool"""
    
    # Application Settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Database Settings
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///trading_data.db'
    
    # Broker API Keys
    ANGEL_ONE_CLIENT_ID = os.environ.get('ANGEL_ONE_CLIENT_ID')
    ANGEL_ONE_PASSWORD = os.environ.get('ANGEL_ONE_PASSWORD')
    ANGEL_ONE_API_KEY = os.environ.get('ANGEL_ONE_API_KEY')
    ANGEL_ONE_SECRET_KEY = os.environ.get('ANGEL_ONE_SECRET_KEY')
    
    DHAN_CLIENT_ID = os.environ.get('DHAN_CLIENT_ID')
    DHAN_ACCESS_TOKEN = os.environ.get('DHAN_ACCESS_TOKEN')
    
    # Data Source Settings
    ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY')
    POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY')
    TWELVEDATA_API_KEY = os.environ.get('TWELVEDATA_API_KEY')
    
    # Trading Settings
    DEFAULT_CAPITAL = float(os.environ.get('DEFAULT_CAPITAL', '100000'))
    MAX_RISK_PER_TRADE = float(os.environ.get('MAX_RISK_PER_TRADE', '0.02'))  # 2%
    MAX_PORTFOLIO_RISK = float(os.environ.get('MAX_PORTFOLIO_RISK', '0.06'))  # 6%
    
    # Strategy Settings
    DEFAULT_TIMEFRAME = os.environ.get('DEFAULT_TIMEFRAME', '1m')
    LOOKBACK_PERIOD = int(os.environ.get('LOOKBACK_PERIOD', '50'))
    
    # Risk Management
    DEFAULT_STOP_LOSS = float(os.environ.get('DEFAULT_STOP_LOSS', '0.02'))  # 2%
    DEFAULT_TARGET = float(os.environ.get('DEFAULT_TARGET', '0.04'))  # 4%
    TRAILING_STOP = bool(os.environ.get('TRAILING_STOP', 'True'))
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/trading.log')
    
    # Redis Settings (for real-time data caching)
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # Market Hours (IST)
    MARKET_OPEN_TIME = "09:15"
    MARKET_CLOSE_TIME = "15:30"
    
    # Instruments to trade
    DEFAULT_INDICES = ['NIFTY', 'BANKNIFTY', 'FINNIFTY']
    
    # Options settings
    MAX_STRIKES_TO_MONITOR = int(os.environ.get('MAX_STRIKES_TO_MONITOR', '10'))
    MIN_TIME_TO_EXPIRY = int(os.environ.get('MIN_TIME_TO_EXPIRY', '1'))  # days
    
class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DATABASE_URL = 'sqlite:///test_trading.db'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}