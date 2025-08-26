import yfinance as yf
import pandas as pd
import numpy as np
import requests
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Union
import threading
from queue import Queue
import redis
from config.config import Config
from src.utils.logger import setup_logger

class DataManager:
    """
    Comprehensive data manager for fetching market data from multiple sources
    Supports both delayed (free) and real-time (paid) data sources
    """
    
    def __init__(self):
        self.logger = setup_logger('DataManager')
        self.config = Config()
        
        # Initialize Redis for caching (optional)
        try:
            self.redis_client = redis.from_url(self.config.REDIS_URL)
            self.redis_available = True
        except:
            self.redis_client = None
            self.redis_available = False
            self.logger.warning("Redis not available, using in-memory cache")
        
        # In-memory cache as fallback
        self.cache = {}
        self.cache_expiry = {}
        
        # Data sources configuration
        self.data_sources = {
            'yahoo': {'enabled': True, 'delay': 15},  # 15 minutes delay
            'alpha_vantage': {
                'enabled': bool(self.config.ALPHA_VANTAGE_API_KEY),
                'delay': 0,
                'rate_limit': 5  # 5 requests per minute
            },
            'polygon': {
                'enabled': bool(self.config.POLYGON_API_KEY),
                'delay': 0
            },
            'twelvedata': {
                'enabled': bool(self.config.TWELVEDATA_API_KEY),
                'delay': 0,
                'rate_limit': 8  # 8 requests per minute for free tier
            }
        }
        
        # Rate limiting
        self.last_request_time = {}
        
        self.logger.info("DataManager initialized")
    
    def get_real_time_data(self, symbol: str, source: str = 'auto') -> Optional[Dict]:
        """
        Get real-time or delayed market data for a symbol
        
        Args:
            symbol (str): Symbol to fetch data for
            source (str): Data source to use ('auto', 'yahoo', 'alpha_vantage', etc.)
        
        Returns:
            Dict: Market data including OHLCV, technical indicators
        """
        try:
            # Check cache first
            cached_data = self._get_cached_data(symbol)
            if cached_data:
                return cached_data
            
            # Determine which data source to use
            if source == 'auto':
                source = self._select_best_source()
            
            # Fetch data based on source
            if source == 'yahoo':
                data = self._fetch_yahoo_data(symbol)
            elif source == 'alpha_vantage':
                data = self._fetch_alpha_vantage_data(symbol)
            elif source == 'polygon':
                data = self._fetch_polygon_data(symbol)
            elif source == 'twelvedata':
                data = self._fetch_twelvedata_data(symbol)
            else:
                # Fallback to Yahoo Finance
                data = self._fetch_yahoo_data(symbol)
            
            if data:
                # Add technical indicators
                data = self._add_technical_indicators(data)
                
                # Cache the data
                self._cache_data(symbol, data)
                
                return data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return None
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str, 
                          interval: str = '1m') -> Optional[pd.DataFrame]:
        """
        Get historical data for backtesting
        
        Args:
            symbol (str): Symbol to fetch data for
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            interval (str): Data interval ('1m', '5m', '15m', '1h', '1d')
        
        Returns:
            pd.DataFrame: Historical OHLCV data
        """
        try:
            self.logger.info(f"Fetching historical data for {symbol} from {start_date} to {end_date}")
            
            # Use Yahoo Finance for historical data (free and reliable)
            ticker = yf.Ticker(symbol)
            data = ticker.history(
                start=start_date,
                end=end_date,
                interval=interval,
                auto_adjust=True,
                prepost=True
            )
            
            if not data.empty:
                # Standardize column names
                data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                data = data.dropna()
                
                self.logger.info(f"Fetched {len(data)} records for {symbol}")
                return data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return None
    
    def get_options_chain(self, symbol: str, expiry_date: str = None) -> Optional[Dict]:
        """
        Get options chain data for a symbol
        
        Args:
            symbol (str): Underlying symbol
            expiry_date (str): Specific expiry date (optional)
        
        Returns:
            Dict: Options chain data
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Get available expiry dates
            expiry_dates = ticker.options
            
            if not expiry_dates:
                return None
            
            # Use specified expiry or nearest expiry
            if expiry_date and expiry_date in expiry_dates:
                target_expiry = expiry_date
            else:
                target_expiry = expiry_dates[0]  # Nearest expiry
            
            # Get options chain
            options_chain = ticker.option_chain(target_expiry)
            
            calls = options_chain.calls
            puts = options_chain.puts
            
            return {
                'expiry_date': target_expiry,
                'calls': calls.to_dict('records'),
                'puts': puts.to_dict('records'),
                'available_expiries': list(expiry_dates)
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching options chain for {symbol}: {str(e)}")
            return None
    
    def get_nse_indices_data(self) -> Dict:
        """
        Get NSE indices data (NIFTY, BANKNIFTY, etc.)
        This is a placeholder for NSE-specific data sources
        """
        indices = ['NIFTY', 'BANKNIFTY', 'FINNIFTY']
        data = {}
        
        for index in indices:
            # For now, use Yahoo Finance with .NS suffix
            symbol = f"^{index}" if index == 'NIFTY' else f"{index}.NS"
            index_data = self.get_real_time_data(symbol)
            if index_data:
                data[index] = index_data
        
        return data
    
    def _fetch_yahoo_data(self, symbol: str) -> Optional[Dict]:
        """Fetch data from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get current price and basic info
            info = ticker.info
            hist = ticker.history(period="1d", interval="1m")
            
            if hist.empty:
                return None
            
            current_data = hist.iloc[-1]
            
            return {
                'symbol': symbol,
                'price': float(current_data['Close']),
                'open': float(current_data['Open']),
                'high': float(current_data['High']),
                'low': float(current_data['Low']),
                'volume': int(current_data['Volume']),
                'timestamp': datetime.now().isoformat(),
                'source': 'yahoo',
                'delay_minutes': 15,
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'change': float(current_data['Close'] - current_data['Open']),
                'change_percent': ((current_data['Close'] - current_data['Open']) / current_data['Open']) * 100
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching Yahoo data for {symbol}: {str(e)}")
            return None
    
    def _fetch_alpha_vantage_data(self, symbol: str) -> Optional[Dict]:
        """Fetch real-time data from Alpha Vantage"""
        if not self.config.ALPHA_VANTAGE_API_KEY:
            return None
        
        try:
            # Rate limiting
            if not self._check_rate_limit('alpha_vantage'):
                return None
            
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.config.ALPHA_VANTAGE_API_KEY
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if 'Global Quote' in data:
                quote = data['Global Quote']
                return {
                    'symbol': symbol,
                    'price': float(quote['05. price']),
                    'open': float(quote['02. open']),
                    'high': float(quote['03. high']),
                    'low': float(quote['04. low']),
                    'volume': int(quote['06. volume']),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'alpha_vantage',
                    'delay_minutes': 0,
                    'change': float(quote['09. change']),
                    'change_percent': float(quote['10. change percent'].rstrip('%'))
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching Alpha Vantage data for {symbol}: {str(e)}")
            return None
    
    def _fetch_polygon_data(self, symbol: str) -> Optional[Dict]:
        """Fetch real-time data from Polygon.io"""
        if not self.config.POLYGON_API_KEY:
            return None
        
        try:
            url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}"
            params = {
                'apiKey': self.config.POLYGON_API_KEY
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data['status'] == 'OK' and 'results' in data:
                ticker_data = data['results'][0]
                day_data = ticker_data['day']
                
                return {
                    'symbol': symbol,
                    'price': float(ticker_data['value']),
                    'open': float(day_data['o']),
                    'high': float(day_data['h']),
                    'low': float(day_data['l']),
                    'volume': int(day_data['v']),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'polygon',
                    'delay_minutes': 0,
                    'change': float(ticker_data['value'] - day_data['o']),
                    'change_percent': ((ticker_data['value'] - day_data['o']) / day_data['o']) * 100
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching Polygon data for {symbol}: {str(e)}")
            return None
    
    def _fetch_twelvedata_data(self, symbol: str) -> Optional[Dict]:
        """Fetch real-time data from Twelve Data"""
        if not self.config.TWELVEDATA_API_KEY:
            return None
        
        try:
            # Rate limiting
            if not self._check_rate_limit('twelvedata'):
                return None
            
            url = f"https://api.twelvedata.com/quote"
            params = {
                'symbol': symbol,
                'apikey': self.config.TWELVEDATA_API_KEY
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if 'price' in data:
                return {
                    'symbol': symbol,
                    'price': float(data['close']),
                    'open': float(data['open']),
                    'high': float(data['high']),
                    'low': float(data['low']),
                    'volume': int(data['volume']),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'twelvedata',
                    'delay_minutes': 0,
                    'change': float(data['close']) - float(data['previous_close']),
                    'change_percent': float(data['percent_change'])
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching Twelve Data for {symbol}: {str(e)}")
            return None
    
    def _add_technical_indicators(self, data: Dict) -> Dict:
        """Add technical indicators to market data"""
        try:
            # This is a simplified version. For full implementation,
            # you would calculate RSI, MACD, moving averages, etc.
            # For now, we'll add basic indicators
            
            symbol = data['symbol']
            
            # Get recent historical data for indicator calculation
            hist_data = self.get_historical_data(symbol, 
                                               (datetime.now() - timedelta(days=50)).strftime('%Y-%m-%d'),
                                               datetime.now().strftime('%Y-%m-%d'),
                                               '1m')
            
            if hist_data is not None and len(hist_data) > 0:
                # Simple moving averages
                data['sma_20'] = hist_data['Close'].rolling(window=20).mean().iloc[-1] if len(hist_data) >= 20 else None
                data['sma_50'] = hist_data['Close'].rolling(window=50).mean().iloc[-1] if len(hist_data) >= 50 else None
                
                # Calculate RSI (simplified)
                if len(hist_data) >= 14:
                    delta = hist_data['Close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    data['rsi'] = 100 - (100 / (1 + rs.iloc[-1]))
                
                # Volatility (standard deviation of returns)
                returns = hist_data['Close'].pct_change().dropna()
                data['volatility'] = returns.std() * 100 if len(returns) > 0 else None
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error adding technical indicators: {str(e)}")
            return data
    
    def _select_best_source(self) -> str:
        """Select the best available data source based on configuration"""
        # Priority order: real-time sources first, then delayed
        priority_order = ['polygon', 'alpha_vantage', 'twelvedata', 'yahoo']
        
        for source in priority_order:
            if self.data_sources[source]['enabled']:
                return source
        
        # Fallback to Yahoo Finance
        return 'yahoo'
    
    def _check_rate_limit(self, source: str) -> bool:
        """Check if we can make a request without hitting rate limits"""
        current_time = time.time()
        
        if source in self.last_request_time:
            time_diff = current_time - self.last_request_time[source]
            
            # Check source-specific rate limits
            if source == 'alpha_vantage' and time_diff < 12:  # 5 requests per minute
                return False
            elif source == 'twelvedata' and time_diff < 7.5:  # 8 requests per minute
                return False
        
        self.last_request_time[source] = current_time
        return True
    
    def _get_cached_data(self, symbol: str) -> Optional[Dict]:
        """Get cached data if available and not expired"""
        try:
            if self.redis_available:
                cached = self.redis_client.get(f"market_data:{symbol}")
                if cached:
                    data = json.loads(cached)
                    # Check if data is still fresh (1 minute cache)
                    cached_time = datetime.fromisoformat(data['timestamp'])
                    if (datetime.now() - cached_time).seconds < 60:
                        return data
            else:
                # Use in-memory cache
                if symbol in self.cache:
                    cached_time = self.cache_expiry.get(symbol)
                    if cached_time and (datetime.now() - cached_time).seconds < 60:
                        return self.cache[symbol]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting cached data: {str(e)}")
    
    def _cache_data(self, symbol: str, data: Dict):
        """Cache market data"""
        try:
            if self.redis_available:
                self.redis_client.setex(
                    f"market_data:{symbol}",
                    60,  # 1 minute expiry
                    json.dumps(data, default=str)
                )
            else:
                # Use in-memory cache
                self.cache[symbol] = data
                self.cache_expiry[symbol] = datetime.now()
                
        except Exception as e:
            self.logger.error(f"Error caching data: {str(e)}")