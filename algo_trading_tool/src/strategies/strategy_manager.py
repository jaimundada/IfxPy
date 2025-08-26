import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import threading
import time

from src.strategies.options_strategies import OptionsStrategies
from src.strategies.technical_indicators import TechnicalIndicators
from src.strategies.momentum_strategy import MomentumStrategy
from src.strategies.mean_reversion_strategy import MeanReversionStrategy
from src.strategies.volatility_strategy import VolatilityStrategy
from src.data_sources.data_manager import DataManager
from src.utils.logger import setup_logger
from config.config import Config

class StrategyManager:
    """
    Manages multiple trading strategies and provides intelligent trade selection
    Automatically selects optimal strikes, manages entries/exits, and risk
    """
    
    def __init__(self):
        self.logger = setup_logger('StrategyManager')
        self.config = Config()
        self.data_manager = DataManager()
        
        # Initialize strategy components
        self.options_strategies = OptionsStrategies()
        self.technical_indicators = TechnicalIndicators()
        self.momentum_strategy = MomentumStrategy()
        self.mean_reversion_strategy = MeanReversionStrategy()
        self.volatility_strategy = VolatilityStrategy()
        
        # Strategy configuration
        self.active_strategies = {
            'momentum': True,
            'mean_reversion': True,
            'volatility': True,
            'options_selling': True,
            'options_buying': True
        }
        
        # Current positions tracking
        self.active_positions = {}
        self.position_history = []
        
        # Market regime detection
        self.market_regime = 'neutral'  # 'bullish', 'bearish', 'neutral', 'high_vol'
        
        self.logger.info("StrategyManager initialized")
    
    def analyze_symbol(self, symbol: str, market_data: Dict) -> List[Dict]:
        """
        Analyze a symbol and generate trading signals
        
        Args:
            symbol (str): Symbol to analyze
            market_data (Dict): Current market data
        
        Returns:
            List[Dict]: List of trading signals
        """
        try:
            signals = []
            
            # Get historical data for analysis
            historical_data = self._get_analysis_data(symbol)
            if historical_data is None or historical_data.empty:
                return signals
            
            # Detect market regime
            self._detect_market_regime(symbol, historical_data, market_data)
            
            # Generate signals from different strategies
            if self.active_strategies.get('momentum'):
                momentum_signals = self.momentum_strategy.generate_signals(
                    symbol, historical_data, market_data
                )
                signals.extend(momentum_signals)
            
            if self.active_strategies.get('mean_reversion'):
                mean_reversion_signals = self.mean_reversion_strategy.generate_signals(
                    symbol, historical_data, market_data
                )
                signals.extend(mean_reversion_signals)
            
            if self.active_strategies.get('volatility'):
                volatility_signals = self.volatility_strategy.generate_signals(
                    symbol, historical_data, market_data
                )
                signals.extend(volatility_signals)
            
            # Generate options signals for indices
            if symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']:
                if self.active_strategies.get('options_selling'):
                    options_sell_signals = self._generate_options_selling_signals(
                        symbol, historical_data, market_data
                    )
                    signals.extend(options_sell_signals)
                
                if self.active_strategies.get('options_buying'):
                    options_buy_signals = self._generate_options_buying_signals(
                        symbol, historical_data, market_data
                    )
                    signals.extend(options_buy_signals)
            
            # Filter and rank signals
            filtered_signals = self._filter_and_rank_signals(signals, symbol, market_data)
            
            return filtered_signals
            
        except Exception as e:
            self.logger.error(f"Error analyzing symbol {symbol}: {str(e)}")
            return []
    
    def check_exit_conditions(self, symbol: str, position: Dict) -> Optional[Dict]:
        """
        Check if any exit conditions are met for existing positions
        
        Args:
            symbol (str): Symbol of the position
            position (Dict): Position details
        
        Returns:
            Optional[Dict]: Exit signal if conditions are met
        """
        try:
            # Get current market data
            current_data = self.data_manager.get_real_time_data(symbol)
            if not current_data:
                return None
            
            # Get historical data for analysis
            historical_data = self._get_analysis_data(symbol)
            if historical_data is None or historical_data.empty:
                return None
            
            current_price = current_data['price']
            entry_price = position.get('entry_price', 0)
            entry_time = position.get('entry_time')
            position_type = position.get('type')  # 'BUY' or 'SELL'
            strategy_type = position.get('strategy')
            
            # Calculate current P&L
            if position_type == 'BUY':
                pnl_percent = ((current_price - entry_price) / entry_price) * 100
            else:
                pnl_percent = ((entry_price - current_price) / entry_price) * 100
            
            # Time-based exit (maximum holding period)
            if entry_time:
                entry_datetime = datetime.fromisoformat(entry_time)
                holding_hours = (datetime.now() - entry_datetime).total_seconds() / 3600
                
                # Exit after maximum holding period (configurable)
                max_holding_hours = position.get('max_holding_hours', 24)
                if holding_hours > max_holding_hours:
                    return self._create_exit_signal(
                        symbol, position, 'time_exit', 
                        'Maximum holding period reached'
                    )
            
            # Profit target exit
            target_percent = position.get('target_percent', self.config.DEFAULT_TARGET * 100)
            if pnl_percent >= target_percent:
                return self._create_exit_signal(
                    symbol, position, 'profit_target', 
                    f'Profit target of {target_percent}% reached'
                )
            
            # Stop loss exit
            stop_loss_percent = position.get('stop_loss_percent', self.config.DEFAULT_STOP_LOSS * 100)
            if pnl_percent <= -stop_loss_percent:
                return self._create_exit_signal(
                    symbol, position, 'stop_loss', 
                    f'Stop loss of {stop_loss_percent}% hit'
                )
            
            # Trailing stop loss
            if position.get('trailing_stop', False):
                trailing_stop_signal = self._check_trailing_stop(position, current_price)
                if trailing_stop_signal:
                    return trailing_stop_signal
            
            # Strategy-specific exit conditions
            if strategy_type == 'momentum':
                momentum_exit = self.momentum_strategy.check_exit_conditions(
                    symbol, position, historical_data, current_data
                )
                if momentum_exit:
                    return momentum_exit
            
            elif strategy_type == 'mean_reversion':
                mean_reversion_exit = self.mean_reversion_strategy.check_exit_conditions(
                    symbol, position, historical_data, current_data
                )
                if mean_reversion_exit:
                    return mean_reversion_exit
            
            elif strategy_type == 'volatility':
                volatility_exit = self.volatility_strategy.check_exit_conditions(
                    symbol, position, historical_data, current_data
                )
                if volatility_exit:
                    return volatility_exit
            
            # Options-specific exit conditions
            if position.get('instrument_type') == 'options':
                options_exit = self._check_options_exit_conditions(position, current_data)
                if options_exit:
                    return options_exit
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking exit conditions for {symbol}: {str(e)}")
            return None
    
    def _generate_options_selling_signals(self, symbol: str, historical_data: pd.DataFrame, 
                                        market_data: Dict) -> List[Dict]:
        """Generate options selling signals (premium collection strategies)"""
        signals = []
        
        try:
            # Get options chain
            options_chain = self.data_manager.get_options_chain(symbol)
            if not options_chain:
                return signals
            
            current_price = market_data['price']
            volatility = market_data.get('volatility', 20)
            
            # Calculate optimal strikes for selling
            optimal_strikes = self.options_strategies.find_optimal_selling_strikes(
                current_price, options_chain, volatility
            )
            
            # Check market conditions for options selling
            if self._is_favorable_for_options_selling(historical_data, market_data):
                
                # Generate strangle selling signals
                if optimal_strikes.get('strangle'):
                    strangle_signal = {
                        'symbol': symbol,
                        'strategy': 'short_strangle',
                        'type': 'SELL',
                        'instrument_type': 'options',
                        'legs': [
                            {
                                'option_type': 'CE',
                                'strike': optimal_strikes['strangle']['call_strike'],
                                'action': 'SELL'
                            },
                            {
                                'option_type': 'PE',
                                'strike': optimal_strikes['strangle']['put_strike'],
                                'action': 'SELL'
                            }
                        ],
                        'confidence': optimal_strikes['strangle']['confidence'],
                        'expected_profit': optimal_strikes['strangle']['max_profit'],
                        'max_loss': optimal_strikes['strangle']['max_loss'],
                        'entry_reason': 'High IV, favorable market conditions for premium selling',
                        'target_percent': 50,  # Target 50% of max profit
                        'stop_loss_percent': 200,  # Stop at 200% of premium received
                        'max_holding_hours': 720  # 30 days max
                    }
                    signals.append(strangle_signal)
                
                # Generate iron condor signals for low volatility
                if volatility < 15 and optimal_strikes.get('iron_condor'):
                    iron_condor_signal = {
                        'symbol': symbol,
                        'strategy': 'iron_condor',
                        'type': 'SELL',
                        'instrument_type': 'options',
                        'legs': optimal_strikes['iron_condor']['legs'],
                        'confidence': optimal_strikes['iron_condor']['confidence'],
                        'expected_profit': optimal_strikes['iron_condor']['max_profit'],
                        'max_loss': optimal_strikes['iron_condor']['max_loss'],
                        'entry_reason': 'Low volatility, range-bound market',
                        'target_percent': 50,
                        'stop_loss_percent': 200,
                        'max_holding_hours': 720
                    }
                    signals.append(iron_condor_signal)
            
        except Exception as e:
            self.logger.error(f"Error generating options selling signals: {str(e)}")
        
        return signals
    
    def _generate_options_buying_signals(self, symbol: str, historical_data: pd.DataFrame, 
                                       market_data: Dict) -> List[Dict]:
        """Generate options buying signals (directional strategies)"""
        signals = []
        
        try:
            # Get options chain
            options_chain = self.data_manager.get_options_chain(symbol)
            if not options_chain:
                return signals
            
            current_price = market_data['price']
            
            # Detect strong directional moves
            direction = self._detect_directional_bias(historical_data, market_data)
            
            if direction != 'neutral':
                # Calculate optimal strikes for buying
                optimal_strikes = self.options_strategies.find_optimal_buying_strikes(
                    current_price, options_chain, direction
                )
                
                if optimal_strikes:
                    option_type = 'CE' if direction == 'bullish' else 'PE'
                    strike = optimal_strikes['strike']
                    confidence = optimal_strikes['confidence']
                    
                    options_buy_signal = {
                        'symbol': symbol,
                        'strategy': f'{direction}_options_buy',
                        'type': 'BUY',
                        'instrument_type': 'options',
                        'option_type': option_type,
                        'strike': strike,
                        'confidence': confidence,
                        'entry_reason': f'Strong {direction} momentum detected',
                        'target_percent': 100,  # Target 100% profit
                        'stop_loss_percent': 50,  # Stop at 50% loss
                        'max_holding_hours': 24,  # 1 day max for buying
                        'trailing_stop': True
                    }
                    signals.append(options_buy_signal)
            
        except Exception as e:
            self.logger.error(f"Error generating options buying signals: {str(e)}")
        
        return signals
    
    def _detect_market_regime(self, symbol: str, historical_data: pd.DataFrame, 
                            market_data: Dict):
        """Detect current market regime for strategy selection"""
        try:
            # Calculate various market indicators
            volatility = market_data.get('volatility', 20)
            recent_returns = historical_data['Close'].pct_change().tail(20)
            
            # Volatility regime
            if volatility > 25:
                vol_regime = 'high'
            elif volatility < 12:
                vol_regime = 'low'
            else:
                vol_regime = 'medium'
            
            # Trend regime
            sma_20 = historical_data['Close'].rolling(20).mean().iloc[-1]
            sma_50 = historical_data['Close'].rolling(50).mean().iloc[-1]
            current_price = market_data['price']
            
            if current_price > sma_20 > sma_50:
                trend_regime = 'bullish'
            elif current_price < sma_20 < sma_50:
                trend_regime = 'bearish'
            else:
                trend_regime = 'neutral'
            
            # Combine regimes
            if vol_regime == 'high':
                self.market_regime = 'high_vol'
            else:
                self.market_regime = trend_regime
            
            self.logger.debug(f"Market regime for {symbol}: {self.market_regime}")
            
        except Exception as e:
            self.logger.error(f"Error detecting market regime: {str(e)}")
    
    def _filter_and_rank_signals(self, signals: List[Dict], symbol: str, 
                               market_data: Dict) -> List[Dict]:
        """Filter and rank signals based on confidence and market conditions"""
        try:
            if not signals:
                return signals
            
            # Filter signals based on minimum confidence
            min_confidence = 0.6
            filtered_signals = [s for s in signals if s.get('confidence', 0) >= min_confidence]
            
            # Avoid conflicting signals
            filtered_signals = self._remove_conflicting_signals(filtered_signals)
            
            # Rank by confidence and expected return
            for signal in filtered_signals:
                # Calculate ranking score
                confidence = signal.get('confidence', 0)
                expected_return = signal.get('expected_profit', 0)
                risk_reward = expected_return / max(signal.get('max_loss', 1), 1)
                
                signal['ranking_score'] = confidence * 0.4 + risk_reward * 0.6
            
            # Sort by ranking score
            filtered_signals.sort(key=lambda x: x.get('ranking_score', 0), reverse=True)
            
            # Limit number of signals
            return filtered_signals[:3]  # Top 3 signals
            
        except Exception as e:
            self.logger.error(f"Error filtering signals: {str(e)}")
            return signals
    
    def _remove_conflicting_signals(self, signals: List[Dict]) -> List[Dict]:
        """Remove conflicting signals (e.g., both buy and sell for same symbol)"""
        try:
            # Group by symbol and strategy type
            signal_groups = {}
            
            for signal in signals:
                key = f"{signal['symbol']}_{signal.get('instrument_type', 'equity')}"
                if key not in signal_groups:
                    signal_groups[key] = []
                signal_groups[key].append(signal)
            
            # For each group, keep only the highest confidence signal
            filtered_signals = []
            for group in signal_groups.values():
                if len(group) == 1:
                    filtered_signals.extend(group)
                else:
                    # Keep the signal with highest confidence
                    best_signal = max(group, key=lambda x: x.get('confidence', 0))
                    filtered_signals.append(best_signal)
            
            return filtered_signals
            
        except Exception as e:
            self.logger.error(f"Error removing conflicting signals: {str(e)}")
            return signals
    
    def _get_analysis_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get historical data for strategy analysis"""
        try:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=100)).strftime('%Y-%m-%d')
            
            data = self.data_manager.get_historical_data(
                symbol, start_date, end_date, '5m'
            )
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error getting analysis data for {symbol}: {str(e)}")
            return None
    
    def _is_favorable_for_options_selling(self, historical_data: pd.DataFrame, 
                                        market_data: Dict) -> bool:
        """Check if market conditions are favorable for options selling"""
        try:
            volatility = market_data.get('volatility', 20)
            
            # Favor selling when:
            # 1. High implied volatility
            # 2. Low realized volatility
            # 3. Range-bound market
            
            if volatility > 20:  # High IV
                # Check if market is range-bound
                recent_high = historical_data['High'].tail(20).max()
                recent_low = historical_data['Low'].tail(20).min()
                current_price = market_data['price']
                
                # If price is in middle 60% of recent range
                range_position = (current_price - recent_low) / (recent_high - recent_low)
                if 0.2 <= range_position <= 0.8:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking options selling conditions: {str(e)}")
            return False
    
    def _detect_directional_bias(self, historical_data: pd.DataFrame, 
                               market_data: Dict) -> str:
        """Detect directional bias for options buying"""
        try:
            # Use multiple indicators to detect strong directional moves
            current_price = market_data['price']
            
            # Moving average crossover
            sma_5 = historical_data['Close'].rolling(5).mean().iloc[-1]
            sma_20 = historical_data['Close'].rolling(20).mean().iloc[-1]
            
            # RSI
            rsi = market_data.get('rsi', 50)
            
            # Recent momentum
            recent_change = (current_price - historical_data['Close'].iloc[-5]) / historical_data['Close'].iloc[-5]
            
            bullish_signals = 0
            bearish_signals = 0
            
            # Check various conditions
            if current_price > sma_5 > sma_20:
                bullish_signals += 1
            elif current_price < sma_5 < sma_20:
                bearish_signals += 1
            
            if rsi > 60:
                bullish_signals += 1
            elif rsi < 40:
                bearish_signals += 1
            
            if recent_change > 0.02:  # 2% move
                bullish_signals += 1
            elif recent_change < -0.02:
                bearish_signals += 1
            
            # Require at least 2 confirming signals
            if bullish_signals >= 2:
                return 'bullish'
            elif bearish_signals >= 2:
                return 'bearish'
            else:
                return 'neutral'
                
        except Exception as e:
            self.logger.error(f"Error detecting directional bias: {str(e)}")
            return 'neutral'
    
    def _create_exit_signal(self, symbol: str, position: Dict, exit_type: str, 
                          reason: str) -> Dict:
        """Create an exit signal for a position"""
        return {
            'symbol': symbol,
            'type': 'SELL' if position.get('type') == 'BUY' else 'BUY',
            'quantity': position.get('quantity', 0),
            'order_type': 'exit',
            'exit_type': exit_type,
            'reason': reason,
            'position_id': position.get('id'),
            'strategy': position.get('strategy'),
            'price_type': 'MARKET'  # Use market order for exits
        }
    
    def _check_trailing_stop(self, position: Dict, current_price: float) -> Optional[Dict]:
        """Check trailing stop conditions"""
        try:
            # Implement trailing stop logic
            # This is a simplified version
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking trailing stop: {str(e)}")
            return None
    
    def _check_options_exit_conditions(self, position: Dict, current_data: Dict) -> Optional[Dict]:
        """Check options-specific exit conditions"""
        try:
            # Check time decay, volatility changes, etc.
            # This would be implemented based on options Greeks
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking options exit conditions: {str(e)}")
            return None
    
    def get_strategy_performance(self) -> Dict:
        """Get performance metrics for all strategies"""
        try:
            # Calculate performance metrics from position history
            # This would include win rate, average return, Sharpe ratio, etc.
            return {
                'total_trades': len(self.position_history),
                'active_positions': len(self.active_positions),
                'win_rate': 0.0,  # Calculate from history
                'avg_return': 0.0,  # Calculate from history
                'sharpe_ratio': 0.0  # Calculate from history
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating strategy performance: {str(e)}")
            return {}