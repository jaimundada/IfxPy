import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from src.strategies.technical_indicators import TechnicalIndicators

class MeanReversionStrategy:
    """Mean reversion trading strategy"""
    
    def __init__(self):
        self.ti = TechnicalIndicators()
    
    def generate_signals(self, symbol: str, historical_data: pd.DataFrame, 
                        market_data: Dict) -> List[Dict]:
        """Generate mean reversion signals"""
        signals = []
        
        try:
            if len(historical_data) < 20:
                return signals
            
            current_price = market_data['price']
            upper, middle, lower = self.ti.bollinger_bands(historical_data['Close'], 20, 2)
            rsi = self.ti.rsi(historical_data['Close']).iloc[-1]
            
            # Oversold condition
            if current_price <= lower.iloc[-1] and rsi < 30:
                signal = {
                    'symbol': symbol,
                    'strategy': 'mean_reversion',
                    'type': 'BUY',
                    'confidence': 0.70,
                    'entry_reason': 'Oversold - price below lower BB, RSI < 30',
                    'target_percent': 3,
                    'stop_loss_percent': 1.5,
                    'max_holding_hours': 24
                }
                signals.append(signal)
            
            # Overbought condition
            elif current_price >= upper.iloc[-1] and rsi > 70:
                signal = {
                    'symbol': symbol,
                    'strategy': 'mean_reversion',
                    'type': 'SELL',
                    'confidence': 0.70,
                    'entry_reason': 'Overbought - price above upper BB, RSI > 70',
                    'target_percent': 3,
                    'stop_loss_percent': 1.5,
                    'max_holding_hours': 24
                }
                signals.append(signal)
            
        except Exception as e:
            pass
        
        return signals
    
    def check_exit_conditions(self, symbol: str, position: Dict, 
                            historical_data: pd.DataFrame, current_data: Dict) -> Optional[Dict]:
        """Check mean reversion exit conditions"""
        return None