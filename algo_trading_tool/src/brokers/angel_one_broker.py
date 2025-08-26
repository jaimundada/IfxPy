import requests
import json
import hashlib
import pyotp
from datetime import datetime
from typing import Dict, List, Optional
from config.config import Config
from src.utils.logger import setup_logger

class AngelOneBroker:
    """
    Angel One (Angel Broking) API integration for trading
    Uses SmartAPI for order execution and portfolio management
    """
    
    def __init__(self):
        self.logger = setup_logger('AngelOneBroker')
        self.config = Config()
        
        # API Configuration
        self.base_url = "https://apiconnect.angelbroking.com"
        self.client_id = self.config.ANGEL_ONE_CLIENT_ID
        self.password = self.config.ANGEL_ONE_PASSWORD
        self.api_key = self.config.ANGEL_ONE_API_KEY
        self.secret_key = self.config.ANGEL_ONE_SECRET_KEY
        
        # Session management
        self.auth_token = None
        self.refresh_token = None
        self.feed_token = None
        self.user_id = None
        
        # Headers
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-UserType': 'USER',
            'X-SourceID': 'WEB',
            'X-ClientLocalIP': '192.168.1.1',
            'X-ClientPublicIP': '106.193.147.98',
            'X-MACAddress': '00:0a:95:9d:68:16',
            'X-PrivateKey': self.api_key
        }
        
        # Login to get session tokens
        self._login()
    
    def _login(self) -> bool:
        """
        Login to Angel One and get session tokens
        
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            login_url = f"{self.base_url}/rest/auth/angelbroking/user/v1/loginByPassword"
            
            # Prepare login data
            login_data = {
                "clientcode": self.client_id,
                "password": self.password
            }
            
            response = requests.post(login_url, headers=self.headers, json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') and data['data']:
                    self.auth_token = data['data']['jwtToken']
                    self.refresh_token = data['data']['refreshToken']
                    self.feed_token = data['data']['feedToken']
                    self.user_id = data['data']['clientcode']
                    
                    # Update headers with auth token
                    self.headers['Authorization'] = f"Bearer {self.auth_token}"
                    
                    self.logger.info("Angel One login successful")
                    return True
                else:
                    self.logger.error(f"Angel One login failed: {data.get('message', 'Unknown error')}")
                    return False
            else:
                self.logger.error(f"Angel One login request failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Angel One login error: {str(e)}")
            return False
    
    def place_order(self, order_data: Dict) -> Dict:
        """
        Place an order on Angel One
        
        Args:
            order_data (Dict): Order details
                - symbol: Trading symbol
                - quantity: Number of shares
                - price: Order price
                - order_type: 'BUY' or 'SELL'
                - product_type: 'MIS', 'CNC', 'NRML'
                - variety: 'NORMAL', 'STOPLOSS', 'AMO'
                - exchange: 'NSE', 'BSE', 'NFO', 'MCX'
        
        Returns:
            Dict: Order execution result
        """
        try:
            order_url = f"{self.base_url}/rest/secure/angelbroking/order/v1/placeOrder"
            
            # Map our order format to Angel One format
            angel_order = {
                "variety": order_data.get('variety', 'NORMAL'),
                "tradingsymbol": order_data['symbol'],
                "symboltoken": self._get_symbol_token(order_data['symbol'], order_data.get('exchange', 'NSE')),
                "transactiontype": order_data['order_type'],
                "exchange": order_data.get('exchange', 'NSE'),
                "ordertype": order_data.get('price_type', 'LIMIT'),
                "producttype": order_data.get('product_type', 'MIS'),
                "duration": order_data.get('duration', 'DAY'),
                "price": str(order_data.get('price', 0)),
                "squareoff": str(order_data.get('square_off', 0)),
                "stoploss": str(order_data.get('stop_loss', 0)),
                "quantity": str(order_data['quantity'])
            }
            
            response = requests.post(order_url, headers=self.headers, json=angel_order)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status'):
                    return {
                        'status': 'success',
                        'order_id': data['data']['orderid'],
                        'message': 'Order placed successfully',
                        'broker_response': data
                    }
                else:
                    return {
                        'status': 'error',
                        'message': data.get('message', 'Order placement failed'),
                        'error_code': data.get('errorcode')
                    }
            else:
                return {
                    'status': 'error',
                    'message': f'HTTP Error: {response.status_code}',
                    'response': response.text
                }
                
        except Exception as e:
            self.logger.error(f"Error placing order: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def modify_order(self, order_id: str, modifications: Dict) -> Dict:
        """
        Modify an existing order
        
        Args:
            order_id (str): Order ID to modify
            modifications (Dict): Modifications to apply
        
        Returns:
            Dict: Modification result
        """
        try:
            modify_url = f"{self.base_url}/rest/secure/angelbroking/order/v1/modifyOrder"
            
            modify_data = {
                "variety": modifications.get('variety', 'NORMAL'),
                "orderid": order_id,
                "ordertype": modifications.get('price_type', 'LIMIT'),
                "producttype": modifications.get('product_type'),
                "duration": modifications.get('duration', 'DAY'),
                "price": str(modifications.get('price', 0)),
                "quantity": str(modifications.get('quantity', 0)),
                "tradingsymbol": modifications.get('symbol'),
                "symboltoken": modifications.get('symbol_token'),
                "exchange": modifications.get('exchange')
            }
            
            response = requests.post(modify_url, headers=self.headers, json=modify_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status'):
                    return {
                        'status': 'success',
                        'order_id': order_id,
                        'message': 'Order modified successfully'
                    }
                else:
                    return {
                        'status': 'error',
                        'message': data.get('message', 'Order modification failed')
                    }
            else:
                return {
                    'status': 'error',
                    'message': f'HTTP Error: {response.status_code}'
                }
                
        except Exception as e:
            self.logger.error(f"Error modifying order: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def cancel_order(self, order_id: str) -> Dict:
        """
        Cancel an existing order
        
        Args:
            order_id (str): Order ID to cancel
        
        Returns:
            Dict: Cancellation result
        """
        try:
            cancel_url = f"{self.base_url}/rest/secure/angelbroking/order/v1/cancelOrder"
            
            cancel_data = {
                "variety": "NORMAL",
                "orderid": order_id
            }
            
            response = requests.post(cancel_url, headers=self.headers, json=cancel_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status'):
                    return {
                        'status': 'success',
                        'order_id': order_id,
                        'message': 'Order cancelled successfully'
                    }
                else:
                    return {
                        'status': 'error',
                        'message': data.get('message', 'Order cancellation failed')
                    }
            else:
                return {
                    'status': 'error',
                    'message': f'HTTP Error: {response.status_code}'
                }
                
        except Exception as e:
            self.logger.error(f"Error cancelling order: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_positions(self) -> List[Dict]:
        """
        Get current positions
        
        Returns:
            List[Dict]: Current positions
        """
        try:
            positions_url = f"{self.base_url}/rest/secure/angelbroking/portfolio/v1/getPosition"
            
            response = requests.get(positions_url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') and data.get('data'):
                    return data['data']
                else:
                    return []
            else:
                self.logger.error(f"Error getting positions: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting positions: {str(e)}")
            return []
    
    def get_orders(self) -> List[Dict]:
        """
        Get order history
        
        Returns:
            List[Dict]: Order history
        """
        try:
            orders_url = f"{self.base_url}/rest/secure/angelbroking/order/v1/getOrderBook"
            
            response = requests.get(orders_url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') and data.get('data'):
                    return data['data']
                else:
                    return []
            else:
                self.logger.error(f"Error getting orders: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting orders: {str(e)}")
            return []
    
    def get_funds(self) -> Dict:
        """
        Get available funds
        
        Returns:
            Dict: Fund details
        """
        try:
            funds_url = f"{self.base_url}/rest/secure/angelbroking/user/v1/getRMS"
            
            response = requests.get(funds_url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') and data.get('data'):
                    return data['data']
                else:
                    return {}
            else:
                self.logger.error(f"Error getting funds: {response.status_code}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting funds: {str(e)}")
            return {}
    
    def get_profile(self) -> Dict:
        """
        Get user profile
        
        Returns:
            Dict: User profile information
        """
        try:
            profile_url = f"{self.base_url}/rest/secure/angelbroking/user/v1/getProfile"
            
            response = requests.get(profile_url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') and data.get('data'):
                    return data['data']
                else:
                    return {}
            else:
                self.logger.error(f"Error getting profile: {response.status_code}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting profile: {str(e)}")
            return {}
    
    def get_instruments(self, exchange: str = None) -> List[Dict]:
        """
        Get available instruments
        
        Args:
            exchange (str): Exchange name (NSE, BSE, NFO, MCX)
        
        Returns:
            List[Dict]: Available instruments
        """
        try:
            # Angel One provides instrument master files
            # This is a simplified implementation
            # In production, you would download and parse the master files
            
            # For now, return common instruments
            instruments = []
            
            if exchange == 'NSE' or exchange is None:
                instruments.extend([
                    {'symbol': 'NIFTY', 'token': '99926000', 'exchange': 'NSE'},
                    {'symbol': 'BANKNIFTY', 'token': '99926009', 'exchange': 'NSE'},
                    {'symbol': 'FINNIFTY', 'token': '99926037', 'exchange': 'NSE'},
                ])
            
            return instruments
            
        except Exception as e:
            self.logger.error(f"Error getting instruments: {str(e)}")
            return []
    
    def calculate_charges(self, symbol: str, quantity: int, price: float, order_type: str) -> Dict:
        """
        Calculate brokerage and other charges
        
        Args:
            symbol (str): Trading symbol
            quantity (int): Number of shares
            price (float): Price per share
            order_type (str): 'BUY' or 'SELL'
        
        Returns:
            Dict: Breakdown of charges
        """
        try:
            gross_value = quantity * price
            
            # Angel One charges (approximate)
            brokerage = min(gross_value * 0.0003, 20)  # 0.03% or Rs. 20, whichever is lower
            stt = gross_value * 0.001 if order_type == 'SELL' else 0  # 0.1% on sell side
            transaction_charges = gross_value * 0.00003  # 0.003%
            gst = (brokerage + transaction_charges) * 0.18  # 18% GST
            sebi_charges = gross_value * 0.000001  # Rs. 1 per crore
            stamp_duty = gross_value * 0.00003 if order_type == 'BUY' else 0  # 0.003% on buy side
            
            total_charges = brokerage + stt + transaction_charges + gst + sebi_charges + stamp_duty
            
            return {
                'brokerage': round(brokerage, 2),
                'stt': round(stt, 2),
                'transaction_charges': round(transaction_charges, 2),
                'gst': round(gst, 2),
                'sebi_charges': round(sebi_charges, 2),
                'stamp_duty': round(stamp_duty, 2),
                'total_charges': round(total_charges, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating charges: {str(e)}")
            return {'total_charges': 0}
    
    def _get_symbol_token(self, symbol: str, exchange: str) -> str:
        """
        Get symbol token for the given symbol and exchange
        
        Args:
            symbol (str): Trading symbol
            exchange (str): Exchange name
        
        Returns:
            str: Symbol token
        """
        # This is a simplified implementation
        # In production, you would have a mapping from the instrument master file
        
        token_mapping = {
            'NIFTY': '99926000',
            'BANKNIFTY': '99926009',
            'FINNIFTY': '99926037'
        }
        
        return token_mapping.get(symbol, '0')
    
    def get_ltp(self, symbol: str, exchange: str = 'NSE') -> float:
        """
        Get Last Traded Price for a symbol
        
        Args:
            symbol (str): Trading symbol
            exchange (str): Exchange name
        
        Returns:
            float: Last traded price
        """
        try:
            ltp_url = f"{self.base_url}/rest/secure/angelbroking/market/v1/getLTP"
            
            ltp_data = {
                "exchange": exchange,
                "tradingsymbol": symbol,
                "symboltoken": self._get_symbol_token(symbol, exchange)
            }
            
            response = requests.post(ltp_url, headers=self.headers, json=ltp_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') and data.get('data'):
                    return float(data['data']['ltp'])
                else:
                    return 0.0
            else:
                self.logger.error(f"Error getting LTP: {response.status_code}")
                return 0.0
                
        except Exception as e:
            self.logger.error(f"Error getting LTP: {str(e)}")
            return 0.0