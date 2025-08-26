import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from src.utils.logger import setup_logger
from config.config import Config

class RiskManager:
    """
    Comprehensive risk management system for algorithmic trading
    Handles position sizing, stop losses, portfolio risk, and exposure limits
    """
    
    def __init__(self):
        self.logger = setup_logger('RiskManager')
        self.config = Config()
        
        # Risk parameters
        self.max_risk_per_trade = self.config.MAX_RISK_PER_TRADE
        self.max_portfolio_risk = self.config.MAX_PORTFOLIO_RISK
        self.max_daily_loss = 0.05  # 5% max daily loss
        
        # Position tracking
        self.current_positions = {}
        self.daily_pnl = 0
        self.portfolio_risk = 0
        
        self.logger.info("RiskManager initialized")
    
    def can_take_position(self, signal: Dict) -> bool:
        """
        Check if a position can be taken based on risk management rules
        
        Args:
            signal (Dict): Trading signal with position details
        
        Returns:
            bool: True if position can be taken, False otherwise
        """
        try:
            # Check individual position risk
            if not self._check_position_risk(signal):
                self.logger.warning("Position rejected due to individual risk limits")
                return False
            
            # Check portfolio risk
            if not self._check_portfolio_risk(signal):
                self.logger.warning("Position rejected due to portfolio risk limits")
                return False
            
            # Check daily loss limits
            if not self._check_daily_loss_limit():
                self.logger.warning("Position rejected due to daily loss limits")
                return False
            
            # Check correlation risk
            if not self._check_correlation_risk(signal):
                self.logger.warning("Position rejected due to correlation risk")
                return False
            
            # Check market hours and conditions
            if not self._check_market_conditions(signal):
                self.logger.warning("Position rejected due to market conditions")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking position risk: {str(e)}")
            return False
    
    def calculate_position_size(self, signal: Dict, account_value: float, 
                              current_price: float) -> int:
        """
        Calculate optimal position size based on risk management
        
        Args:
            signal (Dict): Trading signal
            account_value (float): Current account value
            current_price (float): Current price of the instrument
        
        Returns:
            int: Position size in shares/contracts
        """
        try:
            # Get risk parameters
            stop_loss_percent = signal.get('stop_loss_percent', 2) / 100
            confidence = signal.get('confidence', 0.5)
            
            # Risk-based position sizing
            risk_amount = account_value * self.max_risk_per_trade
            
            # Adjust for confidence
            confidence_adjusted_risk = risk_amount * confidence
            
            # Calculate position size based on stop loss
            if stop_loss_percent > 0:
                position_value = confidence_adjusted_risk / stop_loss_percent
                position_size = int(position_value / current_price)
            else:
                # Fallback to fixed percentage
                position_value = account_value * 0.02  # 2% of account
                position_size = int(position_value / current_price)
            
            # Apply maximum position size limits
            max_position_value = account_value * 0.1  # 10% of account max
            max_position_size = int(max_position_value / current_price)
            
            position_size = min(position_size, max_position_size)
            
            # Minimum position size
            min_position_size = max(1, int(1000 / current_price))  # Minimum $1000 position
            position_size = max(position_size, min_position_size)
            
            self.logger.debug(f"Calculated position size: {position_size} shares for {signal['symbol']}")
            return position_size
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {str(e)}")
            return 0
    
    def update_position(self, position: Dict):
        """Update position in risk manager"""
        try:
            position_id = position.get('id')
            if position_id:
                self.current_positions[position_id] = position
                self._update_portfolio_risk()
                
        except Exception as e:
            self.logger.error(f"Error updating position: {str(e)}")
    
    def remove_position(self, position_id: str):
        """Remove position from risk manager"""
        try:
            if position_id in self.current_positions:
                del self.current_positions[position_id]
                self._update_portfolio_risk()
                
        except Exception as e:
            self.logger.error(f"Error removing position: {str(e)}")
    
    def get_stop_loss_price(self, entry_price: float, position_type: str, 
                           stop_loss_percent: float) -> float:
        """
        Calculate stop loss price
        
        Args:
            entry_price (float): Entry price
            position_type (str): 'BUY' or 'SELL'
            stop_loss_percent (float): Stop loss percentage (as decimal)
        
        Returns:
            float: Stop loss price
        """
        try:
            if position_type == 'BUY':
                return entry_price * (1 - stop_loss_percent)
            else:  # SELL (short)
                return entry_price * (1 + stop_loss_percent)
                
        except Exception as e:
            self.logger.error(f"Error calculating stop loss price: {str(e)}")
            return entry_price
    
    def get_target_price(self, entry_price: float, position_type: str, 
                        target_percent: float) -> float:
        """
        Calculate target price
        
        Args:
            entry_price (float): Entry price
            position_type (str): 'BUY' or 'SELL'
            target_percent (float): Target percentage (as decimal)
        
        Returns:
            float: Target price
        """
        try:
            if position_type == 'BUY':
                return entry_price * (1 + target_percent)
            else:  # SELL (short)
                return entry_price * (1 - target_percent)
                
        except Exception as e:
            self.logger.error(f"Error calculating target price: {str(e)}")
            return entry_price
    
    def check_stop_loss(self, position: Dict, current_price: float) -> bool:
        """
        Check if stop loss should be triggered
        
        Args:
            position (Dict): Position details
            current_price (float): Current market price
        
        Returns:
            bool: True if stop loss should be triggered
        """
        try:
            entry_price = position['entry_price']
            position_type = position['type']
            stop_loss_percent = position.get('stop_loss_percent', 2) / 100
            
            stop_loss_price = self.get_stop_loss_price(entry_price, position_type, stop_loss_percent)
            
            if position_type == 'BUY':
                return current_price <= stop_loss_price
            else:  # SELL (short)
                return current_price >= stop_loss_price
                
        except Exception as e:
            self.logger.error(f"Error checking stop loss: {str(e)}")
            return False
    
    def check_target(self, position: Dict, current_price: float) -> bool:
        """
        Check if target should be triggered
        
        Args:
            position (Dict): Position details
            current_price (float): Current market price
        
        Returns:
            bool: True if target should be triggered
        """
        try:
            entry_price = position['entry_price']
            position_type = position['type']
            target_percent = position.get('target_percent', 5) / 100
            
            target_price = self.get_target_price(entry_price, position_type, target_percent)
            
            if position_type == 'BUY':
                return current_price >= target_price
            else:  # SELL (short)
                return current_price <= target_price
                
        except Exception as e:
            self.logger.error(f"Error checking target: {str(e)}")
            return False
    
    def update_trailing_stop(self, position: Dict, current_price: float) -> Optional[float]:
        """
        Update trailing stop loss
        
        Args:
            position (Dict): Position details
            current_price (float): Current market price
        
        Returns:
            Optional[float]: New trailing stop price if updated
        """
        try:
            if not position.get('trailing_stop', False):
                return None
            
            entry_price = position['entry_price']
            position_type = position['type']
            trailing_percent = position.get('trailing_percent', 1) / 100  # 1% trailing
            
            current_trailing_stop = position.get('trailing_stop_price')
            
            if position_type == 'BUY':
                # For long positions, trailing stop moves up with price
                new_trailing_stop = current_price * (1 - trailing_percent)
                
                if current_trailing_stop is None or new_trailing_stop > current_trailing_stop:
                    position['trailing_stop_price'] = new_trailing_stop
                    return new_trailing_stop
            else:  # SELL (short)
                # For short positions, trailing stop moves down with price
                new_trailing_stop = current_price * (1 + trailing_percent)
                
                if current_trailing_stop is None or new_trailing_stop < current_trailing_stop:
                    position['trailing_stop_price'] = new_trailing_stop
                    return new_trailing_stop
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error updating trailing stop: {str(e)}")
            return None
    
    def _check_position_risk(self, signal: Dict) -> bool:
        """Check individual position risk limits"""
        try:
            # Check confidence threshold
            min_confidence = 0.5
            if signal.get('confidence', 0) < min_confidence:
                return False
            
            # Check stop loss is reasonable
            stop_loss_percent = signal.get('stop_loss_percent', 2)
            if stop_loss_percent > 10:  # Max 10% stop loss
                return False
            
            # Check risk-reward ratio
            target_percent = signal.get('target_percent', 5)
            if target_percent / stop_loss_percent < 1.5:  # Min 1.5:1 risk-reward
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking position risk: {str(e)}")
            return False
    
    def _check_portfolio_risk(self, signal: Dict) -> bool:
        """Check portfolio-level risk limits"""
        try:
            # Check maximum number of positions
            max_positions = 10
            if len(self.current_positions) >= max_positions:
                return False
            
            # Check sector/symbol concentration
            symbol = signal['symbol']
            symbol_positions = sum(1 for p in self.current_positions.values() 
                                 if p.get('symbol') == symbol and p.get('status') == 'open')
            if symbol_positions >= 2:  # Max 2 positions per symbol
                return False
            
            # Check strategy concentration
            strategy = signal.get('strategy', 'unknown')
            strategy_positions = sum(1 for p in self.current_positions.values() 
                                   if p.get('strategy') == strategy and p.get('status') == 'open')
            if strategy_positions >= 3:  # Max 3 positions per strategy
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking portfolio risk: {str(e)}")
            return False
    
    def _check_daily_loss_limit(self) -> bool:
        """Check daily loss limits"""
        try:
            # This would be implemented with real P&L tracking
            # For now, return True
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking daily loss limit: {str(e)}")
            return False
    
    def _check_correlation_risk(self, signal: Dict) -> bool:
        """Check correlation risk with existing positions"""
        try:
            # Check if taking highly correlated positions
            symbol = signal['symbol']
            
            # For Indian indices, check correlation
            correlated_symbols = {
                'NIFTY': ['BANKNIFTY', 'FINNIFTY'],
                'BANKNIFTY': ['NIFTY', 'FINNIFTY'],
                'FINNIFTY': ['NIFTY', 'BANKNIFTY']
            }
            
            if symbol in correlated_symbols:
                correlated = correlated_symbols[symbol]
                
                # Count positions in correlated symbols
                correlated_positions = sum(1 for p in self.current_positions.values() 
                                         if p.get('symbol') in correlated and p.get('status') == 'open')
                
                if correlated_positions >= 2:  # Max 2 correlated positions
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking correlation risk: {str(e)}")
            return True
    
    def _check_market_conditions(self, signal: Dict) -> bool:
        """Check market conditions for trading"""
        try:
            # Check market hours (simplified)
            current_time = datetime.now().time()
            market_open = datetime.strptime("09:15", "%H:%M").time()
            market_close = datetime.strptime("15:30", "%H:%M").time()
            
            # Only trade during market hours
            if not (market_open <= current_time <= market_close):
                return False
            
            # Avoid trading in first and last 15 minutes
            buffer_start = datetime.strptime("09:30", "%H:%M").time()
            buffer_end = datetime.strptime("15:15", "%H:%M").time()
            
            if not (buffer_start <= current_time <= buffer_end):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking market conditions: {str(e)}")
            return True
    
    def _update_portfolio_risk(self):
        """Update portfolio risk metrics"""
        try:
            # Calculate current portfolio risk
            total_risk = 0
            
            for position in self.current_positions.values():
                if position.get('status') == 'open':
                    position_risk = position.get('quantity', 0) * position.get('entry_price', 0)
                    stop_loss_percent = position.get('stop_loss_percent', 2) / 100
                    risk_amount = position_risk * stop_loss_percent
                    total_risk += risk_amount
            
            self.portfolio_risk = total_risk
            
        except Exception as e:
            self.logger.error(f"Error updating portfolio risk: {str(e)}")
    
    def get_risk_metrics(self) -> Dict:
        """Get current risk metrics"""
        try:
            return {
                'portfolio_risk': self.portfolio_risk,
                'active_positions': len([p for p in self.current_positions.values() 
                                       if p.get('status') == 'open']),
                'daily_pnl': self.daily_pnl,
                'max_risk_per_trade': self.max_risk_per_trade,
                'max_portfolio_risk': self.max_portfolio_risk
            }
            
        except Exception as e:
            self.logger.error(f"Error getting risk metrics: {str(e)}")
            return {}
    
    def emergency_stop(self, reason: str = "Emergency stop triggered"):
        """Emergency stop all trading"""
        try:
            self.logger.critical(f"EMERGENCY STOP: {reason}")
            
            # This would trigger immediate closure of all positions
            # and stop all new position taking
            
            for position_id, position in self.current_positions.items():
                if position.get('status') == 'open':
                    self.logger.critical(f"Emergency close required for position: {position_id}")
            
        except Exception as e:
            self.logger.error(f"Error in emergency stop: {str(e)}")
    
    def calculate_var(self, positions: List[Dict], confidence_level: float = 0.05) -> float:
        """
        Calculate Value at Risk (VaR) for the portfolio
        
        Args:
            positions (List[Dict]): List of current positions
            confidence_level (float): Confidence level (default 5%)
        
        Returns:
            float: VaR amount
        """
        try:
            if not positions:
                return 0.0
            
            # Simplified VaR calculation
            # In a real implementation, this would use historical price data
            # and correlation matrices
            
            total_value = sum(p.get('quantity', 0) * p.get('entry_price', 0) for p in positions)
            
            # Assume 2% daily volatility
            daily_volatility = 0.02
            
            # Calculate VaR using normal distribution assumption
            from scipy.stats import norm
            var_multiplier = norm.ppf(confidence_level)
            var_amount = total_value * daily_volatility * abs(var_multiplier)
            
            return var_amount
            
        except Exception as e:
            self.logger.error(f"Error calculating VaR: {str(e)}")
            return 0.0