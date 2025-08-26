import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
from config.config import Config
from src.utils.logger import setup_logger

class DhanBroker:
    """
    Dhan Broker API integration for trading
    Uses Dhan API for order execution and portfolio management
    """
    
    def __init__(self):
        self.logger = setup_logger('DhanBroker')
        self.config = Config()
        
        # API Configuration
        self.base_url = "https://api.dhan.co"
        self.client_id = self.config.DHAN_CLIENT_ID
        self.access_token = self.config.DHAN_ACCESS_TOKEN
        
        # Headers
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'access-token': self.access_token
        }
        
        # Validate connection
        self._validate_connection()
    
    def _validate_connection(self) -> bool:
        """
        Validate the API connection
        
        Returns:
            bool: True if connection is valid, False otherwise
        """
        try:
            # Test the connection by getting user profile
            profile = self.get_profile()
            if profile:
                self.logger.info("Dhan broker connection validated successfully")
                return True
            else:
                self.logger.error("Dhan broker connection validation failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Dhan broker connection error: {str(e)}")
            return False
    
    def place_order(self, order_data: Dict) -> Dict:
        """
        Place an order on Dhan
        
        Args:
            order_data (Dict): Order details
                - symbol: Trading symbol
                - quantity: Number of shares
                - price: Order price
                - order_type: 'BUY' or 'SELL'
                - product_type: 'CNC', 'MIS', 'NRML'
                - price_type: 'MARKET', 'LIMIT', 'SL', 'SL-M'
                - exchange: 'NSE', 'BSE', 'NFO', 'MCX'
        
        Returns:
            Dict: Order execution result
        """
        try:
            order_url = f"{self.base_url}/orders"
            
            # Map our order format to Dhan format
            dhan_order = {
                "dhanClientId": self.client_id,
                "transactionType": order_data['order_type'],
                "exchangeSegment": self._get_exchange_segment(order_data.get('exchange', 'NSE')),
                "productType": order_data.get('product_type', 'MIS'),
                "orderType": order_data.get('price_type', 'LIMIT'),
                "validity": order_data.get('validity', 'DAY'),
                "securityId": self._get_security_id(order_data['symbol'], order_data.get('exchange', 'NSE')),
                "quantity": order_data['quantity'],
                "disclosedQuantity": order_data.get('disclosed_quantity', 0),
                "price": order_data.get('price', 0),
                "triggerPrice": order_data.get('trigger_price', 0),
                "afterMarketOrder": order_data.get('amo', False),
                "boProfitValue": order_data.get('bo_profit', 0),
                "boStopLossValue": order_data.get('bo_stop_loss', 0)
            }
            
            response = requests.post(order_url, headers=self.headers, json=dhan_order)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success':
                    return {
                        'status': 'success',
                        'order_id': data['data']['orderId'],
                        'message': 'Order placed successfully',
                        'broker_response': data
                    }
                else:
                    return {
                        'status': 'error',
                        'message': data.get('remarks', 'Order placement failed')
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
            modify_url = f"{self.base_url}/orders/{order_id}"
            
            modify_data = {
                "dhanClientId": self.client_id,
                "orderId": order_id,
                "orderType": modifications.get('price_type'),
                "legName": modifications.get('leg_name'),
                "quantity": modifications.get('quantity'),
                "price": modifications.get('price'),
                "disclosedQuantity": modifications.get('disclosed_quantity'),
                "triggerPrice": modifications.get('trigger_price'),
                "validity": modifications.get('validity', 'DAY')
            }
            
            response = requests.put(modify_url, headers=self.headers, json=modify_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success':
                    return {
                        'status': 'success',
                        'order_id': order_id,
                        'message': 'Order modified successfully'
                    }
                else:
                    return {
                        'status': 'error',
                        'message': data.get('remarks', 'Order modification failed')
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
            cancel_url = f"{self.base_url}/orders/{order_id}"
            
            response = requests.delete(cancel_url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success':
                    return {
                        'status': 'success',
                        'order_id': order_id,
                        'message': 'Order cancelled successfully'
                    }
                else:
                    return {
                        'status': 'error',
                        'message': data.get('remarks', 'Order cancellation failed')
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
            positions_url = f"{self.base_url}/positions"
            
            response = requests.get(positions_url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success' and data.get('data'):
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
            orders_url = f"{self.base_url}/orders"
            
            response = requests.get(orders_url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success' and data.get('data'):
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
            funds_url = f"{self.base_url}/fundlimit"
            
            response = requests.get(funds_url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success' and data.get('data'):
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
            profile_url = f"{self.base_url}/user"
            
            response = requests.get(profile_url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success' and data.get('data'):
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
            # Dhan provides security master files
            # This is a simplified implementation
            # In production, you would download and parse the master files
            
            # For now, return common instruments
            instruments = []
            
            if exchange == 'NSE' or exchange is None:
                instruments.extend([
                    {'symbol': 'NIFTY 50', 'securityId': '13', 'exchange': 'NSE'},
                    {'symbol': 'NIFTY BANK', 'securityId': '25', 'exchange': 'NSE'},
                    {'symbol': 'NIFTY FIN SERVICE', 'securityId': '1135', 'exchange': 'NSE'},
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
            
            # Dhan charges (approximate)
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
    
    def _get_exchange_segment(self, exchange: str) -> str:
        """
        Get Dhan exchange segment code
        
        Args:
            exchange (str): Exchange name
        
        Returns:
            str: Dhan exchange segment code
        """
        exchange_mapping = {
            'NSE': 'NSE_EQ',
            'BSE': 'BSE_EQ',
            'NFO': 'NSE_FNO',
            'MCX': 'MCX_COMM'
        }
        
        return exchange_mapping.get(exchange, 'NSE_EQ')
    
    def _get_security_id(self, symbol: str, exchange: str) -> str:
        """
        Get security ID for the given symbol and exchange
        
        Args:
            symbol (str): Trading symbol
            exchange (str): Exchange name
        
        Returns:
            str: Security ID
        """
        # This is a simplified implementation
        # In production, you would have a mapping from the security master file
        
        security_mapping = {
            'NIFTY': '13',
            'BANKNIFTY': '25',
            'FINNIFTY': '1135'
        }
        
        return security_mapping.get(symbol, '0')
    
    def get_quote(self, symbol: str, exchange: str = 'NSE') -> Dict:
        """
        Get quote data for a symbol
        
        Args:
            symbol (str): Trading symbol
            exchange (str): Exchange name
        
        Returns:
            Dict: Quote data
        """
        try:
            # For Dhan, we need to use the security ID
            security_id = self._get_security_id(symbol, exchange)
            exchange_segment = self._get_exchange_segment(exchange)
            
            quote_url = f"{self.base_url}/marketfeed/quote"
            
            quote_data = {
                "NSE_EQ": [security_id] if exchange_segment == "NSE_EQ" else [],
                "BSE_EQ": [security_id] if exchange_segment == "BSE_EQ" else [],
                "NSE_FNO": [security_id] if exchange_segment == "NSE_FNO" else [],
                "MCX_COMM": [security_id] if exchange_segment == "MCX_COMM" else []
            }
            
            response = requests.post(quote_url, headers=self.headers, json=quote_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success' and data.get('data'):
                    return data['data']
                else:
                    return {}
            else:
                self.logger.error(f"Error getting quote: {response.status_code}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting quote: {str(e)}")
            return {}
    
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
            quote_data = self.get_quote(symbol, exchange)
            
            if quote_data:
                # Extract LTP from quote data
                exchange_segment = self._get_exchange_segment(exchange)
                if exchange_segment in quote_data:
                    security_id = self._get_security_id(symbol, exchange)
                    security_data = quote_data[exchange_segment].get(security_id, {})
                    return float(security_data.get('LTP', 0))
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error getting LTP: {str(e)}")
            return 0.0