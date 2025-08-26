import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import copy

from src.data_sources.data_manager import DataManager
from src.strategies.strategy_manager import StrategyManager
from src.risk_management.risk_manager import RiskManager
from src.utils.logger import setup_logger
from config.config import Config

class BacktestEngine:
    """
    Comprehensive backtesting engine for algorithmic trading strategies
    Simulates real trading conditions with minute-by-minute data processing
    """
    
    def __init__(self):
        self.logger = setup_logger('BacktestEngine')
        self.config = Config()
        self.data_manager = DataManager()
        self.strategy_manager = StrategyManager()
        self.risk_manager = RiskManager()
        
        # Backtesting state
        self.portfolio = None
        self.positions = {}
        self.order_history = []
        self.trade_history = []
        self.equity_curve = []
        self.performance_metrics = {}
        
        self.logger.info("BacktestEngine initialized")
    
    def run_backtest(self, config: Dict) -> Dict:
        """
        Run a complete backtest simulation
        
        Args:
            config (Dict): Backtest configuration
                - start_date: Start date (YYYY-MM-DD)
                - end_date: End date (YYYY-MM-DD)
                - symbol: Symbol to backtest
                - strategy: Strategy configuration
                - initial_capital: Starting capital
                - position_size: Position sizing method
        
        Returns:
            Dict: Backtest results with performance metrics
        """
        try:
            self.logger.info(f"Starting backtest: {config['symbol']} from {config['start_date']} to {config['end_date']}")
            
            # Initialize backtest
            self._initialize_backtest(config)
            
            # Get historical data
            historical_data = self._get_backtest_data(config)
            if historical_data is None or historical_data.empty:
                return {'error': 'No historical data available for the specified period'}
            
            # Run simulation
            self._run_simulation(historical_data, config)
            
            # Calculate performance metrics
            performance = self._calculate_performance_metrics()
            
            # Generate results
            results = {
                'status': 'success',
                'config': config,
                'performance': performance,
                'trades': self.trade_history,
                'equity_curve': self.equity_curve,
                'positions': self.positions,
                'final_portfolio_value': self.portfolio['total_value'],
                'total_return': performance['total_return'],
                'sharpe_ratio': performance['sharpe_ratio'],
                'max_drawdown': performance['max_drawdown'],
                'win_rate': performance['win_rate'],
                'profit_factor': performance['profit_factor']
            }
            
            self.logger.info(f"Backtest completed. Total return: {performance['total_return']:.2%}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error running backtest: {str(e)}")
            return {'error': str(e)}
    
    def _initialize_backtest(self, config: Dict):
        """Initialize backtest state"""
        initial_capital = config.get('initial_capital', self.config.DEFAULT_CAPITAL)
        
        self.portfolio = {
            'cash': initial_capital,
            'positions_value': 0,
            'total_value': initial_capital,
            'initial_capital': initial_capital
        }
        
        self.positions = {}
        self.order_history = []
        self.trade_history = []
        self.equity_curve = []
        self.performance_metrics = {}
        
        # Configure strategy manager for backtest
        strategy_config = config.get('strategy', {})
        if 'active_strategies' in strategy_config:
            self.strategy_manager.active_strategies.update(strategy_config['active_strategies'])
    
    def _get_backtest_data(self, config: Dict) -> Optional[pd.DataFrame]:
        """Get historical data for backtesting"""
        try:
            symbol = config['symbol']
            start_date = config['start_date']
            end_date = config['end_date']
            interval = config.get('interval', '1m')
            
            data = self.data_manager.get_historical_data(symbol, start_date, end_date, interval)
            
            if data is not None and not data.empty:
                # Add timestamp index if not present
                if not isinstance(data.index, pd.DatetimeIndex):
                    data.index = pd.to_datetime(data.index)
                
                # Sort by timestamp
                data = data.sort_index()
                
                self.logger.info(f"Retrieved {len(data)} data points for {symbol}")
                return data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting backtest data: {str(e)}")
            return None
    
    def _run_simulation(self, data: pd.DataFrame, config: Dict):
        """Run the main simulation loop"""
        try:
            symbol = config['symbol']
            total_bars = len(data)
            
            for i, (timestamp, bar) in enumerate(data.iterrows()):
                # Progress logging
                if i % 1000 == 0:
                    progress = (i / total_bars) * 100
                    self.logger.debug(f"Backtest progress: {progress:.1f}%")
                
                # Create market data dict
                market_data = {
                    'symbol': symbol,
                    'timestamp': timestamp.isoformat(),
                    'price': bar['Close'],
                    'open': bar['Open'],
                    'high': bar['High'],
                    'low': bar['Low'],
                    'volume': bar['Volume']
                }
                
                # Add technical indicators using historical data up to current point
                historical_subset = data.iloc[:i+1]
                if len(historical_subset) >= 50:  # Minimum data for indicators
                    market_data.update(self._calculate_live_indicators(historical_subset))
                
                # Process current timestamp
                self._process_timestamp(timestamp, market_data, historical_subset, config)
                
                # Update equity curve
                self._update_equity_curve(timestamp, market_data)
        
        except Exception as e:
            self.logger.error(f"Error in simulation: {str(e)}")
    
    def _process_timestamp(self, timestamp: pd.Timestamp, market_data: Dict, 
                          historical_data: pd.DataFrame, config: Dict):
        """Process a single timestamp in the backtest"""
        try:
            symbol = config['symbol']
            
            # Check exit conditions for existing positions
            self._check_exit_conditions(timestamp, market_data, historical_data)
            
            # Generate new signals
            signals = self.strategy_manager.analyze_symbol(symbol, market_data)
            
            # Process signals
            for signal in signals:
                if self._should_execute_signal(signal, market_data):
                    self._execute_signal(timestamp, signal, market_data, config)
            
        except Exception as e:
            self.logger.error(f"Error processing timestamp {timestamp}: {str(e)}")
    
    def _check_exit_conditions(self, timestamp: pd.Timestamp, market_data: Dict, 
                             historical_data: pd.DataFrame):
        """Check exit conditions for existing positions"""
        try:
            positions_to_close = []
            
            for position_id, position in self.positions.items():
                if position['status'] != 'open':
                    continue
                
                # Check strategy-specific exit conditions
                exit_signal = self.strategy_manager.check_exit_conditions(
                    position['symbol'], position
                )
                
                if exit_signal:
                    exit_signal['timestamp'] = timestamp
                    exit_signal['price'] = market_data['price']
                    positions_to_close.append((position_id, exit_signal))
                
                # Check time-based exit
                elif self._check_time_exit(position, timestamp):
                    exit_signal = {
                        'timestamp': timestamp,
                        'price': market_data['price'],
                        'exit_type': 'time_exit',
                        'reason': 'Maximum holding period reached'
                    }
                    positions_to_close.append((position_id, exit_signal))
            
            # Close positions
            for position_id, exit_signal in positions_to_close:
                self._close_position(position_id, exit_signal)
                
        except Exception as e:
            self.logger.error(f"Error checking exit conditions: {str(e)}")
    
    def _should_execute_signal(self, signal: Dict, market_data: Dict) -> bool:
        """Check if a signal should be executed"""
        try:
            # Risk management checks
            if not self.risk_manager.can_take_position(signal):
                return False
            
            # Avoid duplicate positions
            symbol = signal['symbol']
            strategy = signal.get('strategy', 'unknown')
            
            # Check if we already have a position in this symbol/strategy
            for position in self.positions.values():
                if (position['symbol'] == symbol and 
                    position['strategy'] == strategy and 
                    position['status'] == 'open'):
                    return False
            
            # Portfolio risk checks
            if not self._check_portfolio_risk(signal, market_data):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking signal execution: {str(e)}")
            return False
    
    def _execute_signal(self, timestamp: pd.Timestamp, signal: Dict, 
                       market_data: Dict, config: Dict):
        """Execute a trading signal"""
        try:
            symbol = signal['symbol']
            price = market_data['price']
            
            # Calculate position size
            position_size = self._calculate_position_size(signal, market_data, config)
            
            if position_size <= 0:
                return
            
            # Create position
            position_id = f"{symbol}_{timestamp.strftime('%Y%m%d_%H%M%S')}_{len(self.positions)}"
            
            position = {
                'id': position_id,
                'symbol': symbol,
                'strategy': signal.get('strategy', 'unknown'),
                'type': signal['type'],
                'quantity': position_size,
                'entry_price': price,
                'entry_time': timestamp.isoformat(),
                'entry_reason': signal.get('entry_reason', ''),
                'status': 'open',
                'target_percent': signal.get('target_percent', 5),
                'stop_loss_percent': signal.get('stop_loss_percent', 2),
                'max_holding_hours': signal.get('max_holding_hours', 24),
                'confidence': signal.get('confidence', 0.5),
                'instrument_type': signal.get('instrument_type', 'equity')
            }
            
            # Update portfolio
            trade_value = position_size * price
            
            if signal['type'] == 'BUY':
                self.portfolio['cash'] -= trade_value
                self.portfolio['positions_value'] += trade_value
            else:  # SELL (short)
                self.portfolio['cash'] += trade_value
                self.portfolio['positions_value'] -= trade_value
            
            # Add to positions
            self.positions[position_id] = position
            
            # Record order
            order = {
                'timestamp': timestamp.isoformat(),
                'position_id': position_id,
                'symbol': symbol,
                'type': signal['type'],
                'quantity': position_size,
                'price': price,
                'value': trade_value,
                'status': 'filled',
                'strategy': signal.get('strategy', 'unknown')
            }
            self.order_history.append(order)
            
            self.logger.debug(f"Executed {signal['type']} signal for {symbol} at {price}")
            
        except Exception as e:
            self.logger.error(f"Error executing signal: {str(e)}")
    
    def _close_position(self, position_id: str, exit_signal: Dict):
        """Close an existing position"""
        try:
            position = self.positions[position_id]
            
            if position['status'] != 'open':
                return
            
            exit_price = exit_signal['price']
            exit_time = exit_signal['timestamp']
            
            # Calculate P&L
            entry_price = position['entry_price']
            quantity = position['quantity']
            
            if position['type'] == 'BUY':
                pnl = (exit_price - entry_price) * quantity
                trade_value = quantity * exit_price
                self.portfolio['cash'] += trade_value
                self.portfolio['positions_value'] -= quantity * entry_price
            else:  # SELL (short)
                pnl = (entry_price - exit_price) * quantity
                trade_value = quantity * exit_price
                self.portfolio['cash'] -= trade_value
                self.portfolio['positions_value'] += quantity * entry_price
            
            # Update position
            position['status'] = 'closed'
            position['exit_price'] = exit_price
            position['exit_time'] = exit_time.isoformat() if hasattr(exit_time, 'isoformat') else exit_time
            position['exit_reason'] = exit_signal.get('reason', 'Unknown')
            position['pnl'] = pnl
            position['pnl_percent'] = (pnl / (entry_price * quantity)) * 100
            position['holding_period'] = self._calculate_holding_period(position)
            
            # Record trade
            trade = copy.deepcopy(position)
            self.trade_history.append(trade)
            
            # Record exit order
            exit_order = {
                'timestamp': exit_time.isoformat() if hasattr(exit_time, 'isoformat') else exit_time,
                'position_id': position_id,
                'symbol': position['symbol'],
                'type': 'SELL' if position['type'] == 'BUY' else 'BUY',
                'quantity': quantity,
                'price': exit_price,
                'value': trade_value,
                'status': 'filled',
                'strategy': position['strategy'],
                'exit_type': exit_signal.get('exit_type', 'unknown')
            }
            self.order_history.append(exit_order)
            
            self.logger.debug(f"Closed position {position_id} with P&L: {pnl:.2f} ({position['pnl_percent']:.2f}%)")
            
        except Exception as e:
            self.logger.error(f"Error closing position {position_id}: {str(e)}")
    
    def _calculate_position_size(self, signal: Dict, market_data: Dict, config: Dict) -> int:
        """Calculate position size based on risk management rules"""
        try:
            price = market_data['price']
            available_cash = self.portfolio['cash']
            
            # Get position sizing method
            sizing_method = config.get('position_sizing', 'fixed_amount')
            
            if sizing_method == 'fixed_amount':
                # Fixed amount per trade
                fixed_amount = config.get('position_amount', 10000)
                return int(min(fixed_amount, available_cash * 0.9) / price)
            
            elif sizing_method == 'percent_capital':
                # Percentage of total capital
                percent = config.get('position_percent', 2) / 100
                return int((self.portfolio['total_value'] * percent) / price)
            
            elif sizing_method == 'risk_based':
                # Risk-based sizing (Kelly Criterion approximation)
                risk_per_trade = config.get('risk_per_trade', 1) / 100  # 1% risk
                stop_loss_percent = signal.get('stop_loss_percent', 2) / 100
                
                risk_amount = self.portfolio['total_value'] * risk_per_trade
                position_value = risk_amount / stop_loss_percent
                
                return int(min(position_value, available_cash * 0.9) / price)
            
            else:
                # Default: fixed amount
                return int(min(10000, available_cash * 0.9) / price)
                
        except Exception as e:
            self.logger.error(f"Error calculating position size: {str(e)}")
            return 0
    
    def _check_portfolio_risk(self, signal: Dict, market_data: Dict) -> bool:
        """Check portfolio-level risk constraints"""
        try:
            # Check maximum portfolio exposure
            total_exposure = abs(self.portfolio['positions_value'])
            max_exposure = self.portfolio['total_value'] * 0.95  # 95% max exposure
            
            if total_exposure >= max_exposure:
                return False
            
            # Check cash availability
            if self.portfolio['cash'] < 1000:  # Minimum cash buffer
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking portfolio risk: {str(e)}")
            return False
    
    def _check_time_exit(self, position: Dict, current_time: pd.Timestamp) -> bool:
        """Check if position should be closed due to time"""
        try:
            entry_time = pd.to_datetime(position['entry_time'])
            max_holding_hours = position.get('max_holding_hours', 24)
            
            holding_hours = (current_time - entry_time).total_seconds() / 3600
            
            return holding_hours >= max_holding_hours
            
        except Exception as e:
            self.logger.error(f"Error checking time exit: {str(e)}")
            return False
    
    def _calculate_holding_period(self, position: Dict) -> float:
        """Calculate holding period in hours"""
        try:
            entry_time = pd.to_datetime(position['entry_time'])
            exit_time = pd.to_datetime(position['exit_time'])
            
            return (exit_time - entry_time).total_seconds() / 3600
            
        except Exception as e:
            self.logger.error(f"Error calculating holding period: {str(e)}")
            return 0.0
    
    def _calculate_live_indicators(self, historical_data: pd.DataFrame) -> Dict:
        """Calculate technical indicators for live data"""
        try:
            indicators = {}
            
            if len(historical_data) >= 14:
                # RSI
                delta = historical_data['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                indicators['rsi'] = rsi.iloc[-1]
            
            if len(historical_data) >= 20:
                # Moving averages
                sma_20 = historical_data['Close'].rolling(window=20).mean().iloc[-1]
                indicators['sma_20'] = sma_20
                
                # Volatility
                returns = historical_data['Close'].pct_change().dropna()
                volatility = returns.std() * np.sqrt(252) * 100  # Annualized volatility
                indicators['volatility'] = volatility
            
            if len(historical_data) >= 50:
                sma_50 = historical_data['Close'].rolling(window=50).mean().iloc[-1]
                indicators['sma_50'] = sma_50
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"Error calculating live indicators: {str(e)}")
            return {}
    
    def _update_equity_curve(self, timestamp: pd.Timestamp, market_data: Dict):
        """Update the equity curve"""
        try:
            # Calculate current portfolio value
            current_positions_value = 0
            current_price = market_data['price']
            
            for position in self.positions.values():
                if position['status'] == 'open':
                    if position['type'] == 'BUY':
                        current_positions_value += position['quantity'] * current_price
                    else:  # SHORT
                        # For short positions, value decreases as price increases
                        entry_value = position['quantity'] * position['entry_price']
                        current_value = position['quantity'] * current_price
                        current_positions_value += (entry_value - current_value)
            
            total_value = self.portfolio['cash'] + current_positions_value
            
            # Update portfolio
            self.portfolio['positions_value'] = current_positions_value
            self.portfolio['total_value'] = total_value
            
            # Add to equity curve
            equity_point = {
                'timestamp': timestamp.isoformat(),
                'total_value': total_value,
                'cash': self.portfolio['cash'],
                'positions_value': current_positions_value,
                'return': ((total_value - self.portfolio['initial_capital']) / self.portfolio['initial_capital']) * 100
            }
            self.equity_curve.append(equity_point)
            
        except Exception as e:
            self.logger.error(f"Error updating equity curve: {str(e)}")
    
    def _calculate_performance_metrics(self) -> Dict:
        """Calculate comprehensive performance metrics"""
        try:
            metrics = {}
            
            if not self.trade_history:
                return {
                    'total_return': 0,
                    'sharpe_ratio': 0,
                    'max_drawdown': 0,
                    'win_rate': 0,
                    'profit_factor': 0,
                    'total_trades': 0
                }
            
            # Basic metrics
            initial_capital = self.portfolio['initial_capital']
            final_value = self.portfolio['total_value']
            
            metrics['total_return'] = ((final_value - initial_capital) / initial_capital) * 100
            metrics['total_trades'] = len(self.trade_history)
            
            # Trade-based metrics
            winning_trades = [t for t in self.trade_history if t['pnl'] > 0]
            losing_trades = [t for t in self.trade_history if t['pnl'] < 0]
            
            metrics['winning_trades'] = len(winning_trades)
            metrics['losing_trades'] = len(losing_trades)
            metrics['win_rate'] = (len(winning_trades) / len(self.trade_history)) * 100 if self.trade_history else 0
            
            # Profit metrics
            total_profit = sum(t['pnl'] for t in winning_trades)
            total_loss = abs(sum(t['pnl'] for t in losing_trades))
            
            metrics['total_profit'] = total_profit
            metrics['total_loss'] = total_loss
            metrics['profit_factor'] = total_profit / total_loss if total_loss > 0 else float('inf')
            
            metrics['avg_win'] = total_profit / len(winning_trades) if winning_trades else 0
            metrics['avg_loss'] = total_loss / len(losing_trades) if losing_trades else 0
            
            # Equity curve based metrics
            if self.equity_curve:
                equity_df = pd.DataFrame(self.equity_curve)
                equity_df['timestamp'] = pd.to_datetime(equity_df['timestamp'])
                equity_df.set_index('timestamp', inplace=True)
                
                # Calculate daily returns
                daily_returns = equity_df['total_value'].resample('D').last().pct_change().dropna()
                
                # Sharpe ratio (assuming risk-free rate of 5%)
                risk_free_rate = 0.05 / 252  # Daily risk-free rate
                excess_returns = daily_returns - risk_free_rate
                metrics['sharpe_ratio'] = (excess_returns.mean() / excess_returns.std() * np.sqrt(252)) if excess_returns.std() > 0 else 0
                
                # Maximum drawdown
                rolling_max = equity_df['total_value'].expanding().max()
                drawdown = (equity_df['total_value'] - rolling_max) / rolling_max * 100
                metrics['max_drawdown'] = abs(drawdown.min())
                
                # Volatility
                metrics['volatility'] = daily_returns.std() * np.sqrt(252) * 100
            
            # Strategy-specific metrics
            strategy_performance = {}
            for trade in self.trade_history:
                strategy = trade.get('strategy', 'unknown')
                if strategy not in strategy_performance:
                    strategy_performance[strategy] = {
                        'trades': 0,
                        'wins': 0,
                        'total_pnl': 0
                    }
                
                strategy_performance[strategy]['trades'] += 1
                strategy_performance[strategy]['total_pnl'] += trade['pnl']
                if trade['pnl'] > 0:
                    strategy_performance[strategy]['wins'] += 1
            
            # Calculate win rates per strategy
            for strategy, perf in strategy_performance.items():
                perf['win_rate'] = (perf['wins'] / perf['trades']) * 100 if perf['trades'] > 0 else 0
            
            metrics['strategy_performance'] = strategy_performance
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {str(e)}")
            return {}