import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from src.strategies.technical_indicators import TechnicalIndicators

class MomentumStrategy:
    """Momentum-based trading strategy"""
    
    def __init__(self):
        self.ti = TechnicalIndicators()
    
    def generate_signals(self, symbol: str, historical_data: pd.DataFrame, 
                        market_data: Dict) -> List[Dict]:
        """Generate momentum-based trading signals"""
        signals = []
        
        try:
            if len(historical_data) < 50:
                return signals
            
            current_price = market_data['price']
            
            # Calculate indicators
            sma_20 = self.ti.sma(historical_data['Close'], 20).iloc[-1]
            sma_50 = self.ti.sma(historical_data['Close'], 50).iloc[-1]
            rsi = self.ti.rsi(historical_data['Close']).iloc[-1]
            
            # Check for momentum conditions
            if current_price > sma_20 > sma_50 and rsi > 60:
                # Bullish momentum
                signal = {
                    'symbol': symbol,
                    'strategy': 'momentum',
                    'type': 'BUY',
                    'confidence': 0.75,
                    'entry_reason': 'Bullish momentum - price above SMAs, RSI > 60',
                    'target_percent': 5,
                    'stop_loss_percent': 2,
                    'max_holding_hours': 48
                }
                signals.append(signal)
            
            elif current_price < sma_20 < sma_50 and rsi < 40:
                # Bearish momentum
                signal = {
                    'symbol': symbol,
                    'strategy': 'momentum',
                    'type': 'SELL',
                    'confidence': 0.75,
                    'entry_reason': 'Bearish momentum - price below SMAs, RSI < 40',
                    'target_percent': 5,
                    'stop_loss_percent': 2,
                    'max_holding_hours': 48
                }
                signals.append(signal)
            
        except Exception as e:
            pass
        
        return signals
    
    def check_exit_conditions(self, symbol: str, position: Dict, 
                            historical_data: pd.DataFrame, current_data: Dict) -> Optional[Dict]:
        """Check momentum-specific exit conditions"""
        return None