import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logger(name='trading_app', log_file='logs/trading.log', level=logging.INFO):
    """
    Set up a comprehensive logger for the trading application
    
    Args:
        name (str): Logger name
        log_file (str): Path to log file
        level: Logging level
    
    Returns:
        logging.Logger: Configured logger instance
    """
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers if they already exist
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_trade(logger, trade_data):
    """
    Log trade execution details
    
    Args:
        logger: Logger instance
        trade_data (dict): Trade information
    """
    logger.info(f"TRADE: {trade_data.get('action', 'UNKNOWN')} "
               f"{trade_data.get('quantity', 0)} "
               f"{trade_data.get('symbol', 'UNKNOWN')} "
               f"@ {trade_data.get('price', 0)} "
               f"[{trade_data.get('order_id', 'NO_ID')}]")

def log_signal(logger, signal_data):
    """
    Log trading signal details
    
    Args:
        logger: Logger instance
        signal_data (dict): Signal information
    """
    logger.info(f"SIGNAL: {signal_data.get('type', 'UNKNOWN')} "
               f"{signal_data.get('symbol', 'UNKNOWN')} "
               f"Strength: {signal_data.get('strength', 0):.2f} "
               f"Price: {signal_data.get('price', 0)}")

def log_error(logger, error_type, error_message, additional_data=None):
    """
    Log error with context
    
    Args:
        logger: Logger instance
        error_type (str): Type of error
        error_message (str): Error message
        additional_data (dict): Additional context data
    """
    error_msg = f"ERROR: {error_type} - {error_message}"
    if additional_data:
        error_msg += f" | Data: {additional_data}"
    
    logger.error(error_msg)

def log_performance(logger, performance_data):
    """
    Log performance metrics
    
    Args:
        logger: Logger instance
        performance_data (dict): Performance metrics
    """
    logger.info(f"PERFORMANCE: "
               f"PnL: {performance_data.get('pnl', 0):.2f} "
               f"Win Rate: {performance_data.get('win_rate', 0):.2f}% "
               f"Trades: {performance_data.get('total_trades', 0)}")