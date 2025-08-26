from typing import Dict, List, Optional
import json
from datetime import datetime
from src.brokers.angel_one_broker import AngelOneBroker
from src.brokers.dhan_broker import DhanBroker
from src.utils.logger import setup_logger
from config.config import Config

class BrokerManager:
    """
    Manages multiple broker connections and provides unified interface
    for order execution and portfolio management
    """
    
    def __init__(self):
        self.logger = setup_logger('BrokerManager')
        self.config = Config()
        
        # Initialize brokers
        self.brokers = {}
        self.active_broker = None
        
        # Initialize Angel One if credentials are available
        if (self.config.ANGEL_ONE_CLIENT_ID and 
            self.config.ANGEL_ONE_PASSWORD and 
            self.config.ANGEL_ONE_API_KEY):
            try:
                self.brokers['angel_one'] = AngelOneBroker()
                self.logger.info("Angel One broker initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Angel One broker: {str(e)}")
        
        # Initialize Dhan if credentials are available
        if (self.config.DHAN_CLIENT_ID and 
            self.config.DHAN_ACCESS_TOKEN):
            try:
                self.brokers['dhan'] = DhanBroker()
                self.logger.info("Dhan broker initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Dhan broker: {str(e)}")
        
        # Set default active broker
        if 'angel_one' in self.brokers:
            self.active_broker = 'angel_one'
        elif 'dhan' in self.brokers:
            self.active_broker = 'dhan'
        
        if self.active_broker:
            self.logger.info(f"Active broker set to: {self.active_broker}")
        else:
            self.logger.warning("No brokers available")
    
    def set_active_broker(self, broker_name: str) -> bool:
        """
        Set the active broker for trading
        
        Args:
            broker_name (str): Name of the broker ('angel_one' or 'dhan')
        
        Returns:
            bool: True if successful, False otherwise
        """
        if broker_name in self.brokers:
            self.active_broker = broker_name
            self.logger.info(f"Active broker changed to: {broker_name}")
            return True
        else:
            self.logger.error(f"Broker {broker_name} not available")
            return False
    
    def place_order(self, order_data: Dict) -> Dict:
        """
        Place an order using the active broker
        
        Args:
            order_data (Dict): Order details including symbol, quantity, price, etc.
        
        Returns:
            Dict: Order execution result
        """
        if not self.active_broker:
            return {
                'status': 'error',
                'message': 'No active broker available'
            }
        
        try:
            broker = self.brokers[self.active_broker]
            result = broker.place_order(order_data)
            
            # Log the order
            self.logger.info(f"Order placed via {self.active_broker}: {order_data}")
            
            return result
            
        except Exception as e:
            error_msg = f"Error placing order: {str(e)}"
            self.logger.error(error_msg)
            return {
                'status': 'error',
                'message': error_msg
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
        if not self.active_broker:
            return {
                'status': 'error',
                'message': 'No active broker available'
            }
        
        try:
            broker = self.brokers[self.active_broker]
            result = broker.modify_order(order_id, modifications)
            
            self.logger.info(f"Order {order_id} modified via {self.active_broker}")
            return result
            
        except Exception as e:
            error_msg = f"Error modifying order: {str(e)}"
            self.logger.error(error_msg)
            return {
                'status': 'error',
                'message': error_msg
            }
    
    def cancel_order(self, order_id: str) -> Dict:
        """
        Cancel an existing order
        
        Args:
            order_id (str): Order ID to cancel
        
        Returns:
            Dict: Cancellation result
        """
        if not self.active_broker:
            return {
                'status': 'error',
                'message': 'No active broker available'
            }
        
        try:
            broker = self.brokers[self.active_broker]
            result = broker.cancel_order(order_id)
            
            self.logger.info(f"Order {order_id} cancelled via {self.active_broker}")
            return result
            
        except Exception as e:
            error_msg = f"Error cancelling order: {str(e)}"
            self.logger.error(error_msg)
            return {
                'status': 'error',
                'message': error_msg
            }
    
    def get_positions(self) -> Dict:
        """
        Get current positions from the active broker
        
        Returns:
            Dict: Current positions
        """
        if not self.active_broker:
            return {
                'status': 'error',
                'message': 'No active broker available'
            }
        
        try:
            broker = self.brokers[self.active_broker]
            positions = broker.get_positions()
            
            return {
                'status': 'success',
                'positions': positions
            }
            
        except Exception as e:
            error_msg = f"Error getting positions: {str(e)}"
            self.logger.error(error_msg)
            return {
                'status': 'error',
                'message': error_msg
            }
    
    def get_orders(self) -> Dict:
        """
        Get order history from the active broker
        
        Returns:
            Dict: Order history
        """
        if not self.active_broker:
            return {
                'status': 'error',
                'message': 'No active broker available'
            }
        
        try:
            broker = self.brokers[self.active_broker]
            orders = broker.get_orders()
            
            return {
                'status': 'success',
                'orders': orders
            }
            
        except Exception as e:
            error_msg = f"Error getting orders: {str(e)}"
            self.logger.error(error_msg)
            return {
                'status': 'error',
                'message': error_msg
            }
    
    def get_funds(self) -> Dict:
        """
        Get available funds from the active broker
        
        Returns:
            Dict: Fund details
        """
        if not self.active_broker:
            return {
                'status': 'error',
                'message': 'No active broker available'
            }
        
        try:
            broker = self.brokers[self.active_broker]
            funds = broker.get_funds()
            
            return {
                'status': 'success',
                'funds': funds
            }
            
        except Exception as e:
            error_msg = f"Error getting funds: {str(e)}"
            self.logger.error(error_msg)
            return {
                'status': 'error',
                'message': error_msg
            }
    
    def get_broker_status(self) -> Dict:
        """
        Get status of all configured brokers
        
        Returns:
            Dict: Status of each broker
        """
        status = {}
        
        for broker_name, broker in self.brokers.items():
            try:
                # Test connection
                broker_status = broker.get_profile()
                status[broker_name] = {
                    'status': 'connected',
                    'profile': broker_status
                }
            except Exception as e:
                status[broker_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return {
            'active_broker': self.active_broker,
            'brokers': status
        }
    
    def calculate_order_value(self, symbol: str, quantity: int, price: float, 
                            order_type: str = 'BUY') -> Dict:
        """
        Calculate the total order value including charges
        
        Args:
            symbol (str): Trading symbol
            quantity (int): Number of shares/contracts
            price (float): Price per unit
            order_type (str): 'BUY' or 'SELL'
        
        Returns:
            Dict: Order value breakdown
        """
        try:
            if not self.active_broker:
                return {
                    'status': 'error',
                    'message': 'No active broker available'
                }
            
            broker = self.brokers[self.active_broker]
            
            # Basic calculation
            gross_value = quantity * price
            
            # Get broker-specific charges (this would be implemented in each broker class)
            charges = broker.calculate_charges(symbol, quantity, price, order_type)
            
            net_value = gross_value + charges.get('total_charges', 0)
            
            return {
                'status': 'success',
                'gross_value': gross_value,
                'charges': charges,
                'net_value': net_value
            }
            
        except Exception as e:
            error_msg = f"Error calculating order value: {str(e)}"
            self.logger.error(error_msg)
            return {
                'status': 'error',
                'message': error_msg
            }
    
    def get_available_instruments(self, exchange: str = None) -> List[Dict]:
        """
        Get list of available instruments for trading
        
        Args:
            exchange (str): Exchange name (NSE, BSE, etc.)
        
        Returns:
            List[Dict]: Available instruments
        """
        if not self.active_broker:
            return []
        
        try:
            broker = self.brokers[self.active_broker]
            instruments = broker.get_instruments(exchange)
            return instruments
            
        except Exception as e:
            self.logger.error(f"Error getting instruments: {str(e)}")
            return []