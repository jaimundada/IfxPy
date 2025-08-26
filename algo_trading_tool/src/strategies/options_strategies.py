import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from src.utils.logger import setup_logger

class OptionsStrategies:
    """
    Intelligent options strategies for automatic strike selection and trade execution
    Implements various options strategies with smart strike selection
    """
    
    def __init__(self):
        self.logger = setup_logger('OptionsStrategies')
    
    def find_optimal_selling_strikes(self, spot_price: float, options_chain: Dict, 
                                   volatility: float) -> Dict:
        """
        Find optimal strikes for options selling strategies
        
        Args:
            spot_price (float): Current spot price
            options_chain (Dict): Options chain data
            volatility (float): Implied volatility
        
        Returns:
            Dict: Optimal strikes for different strategies
        """
        try:
            optimal_strikes = {}
            
            # Get calls and puts data
            calls = options_chain.get('calls', [])
            puts = options_chain.get('puts', [])
            
            if not calls or not puts:
                return optimal_strikes
            
            # Convert to DataFrames for easier manipulation
            calls_df = pd.DataFrame(calls)
            puts_df = pd.DataFrame(puts)
            
            # Short Strangle strategy
            strangle_strikes = self._find_strangle_strikes(spot_price, calls_df, puts_df, volatility)
            if strangle_strikes:
                optimal_strikes['strangle'] = strangle_strikes
            
            # Iron Condor strategy (for low volatility)
            if volatility < 15:
                iron_condor_strikes = self._find_iron_condor_strikes(spot_price, calls_df, puts_df)
                if iron_condor_strikes:
                    optimal_strikes['iron_condor'] = iron_condor_strikes
            
            return optimal_strikes
            
        except Exception as e:
            self.logger.error(f"Error finding optimal selling strikes: {str(e)}")
            return {}
    
    def find_optimal_buying_strikes(self, spot_price: float, options_chain: Dict, 
                                  direction: str) -> Optional[Dict]:
        """
        Find optimal strikes for options buying (directional strategies)
        
        Args:
            spot_price (float): Current spot price
            options_chain (Dict): Options chain data
            direction (str): 'bullish' or 'bearish'
        
        Returns:
            Optional[Dict]: Optimal strike information
        """
        try:
            # Get calls and puts data
            calls = options_chain.get('calls', [])
            puts = options_chain.get('puts', [])
            
            if direction == 'bullish' and calls:
                # Find ATM or slightly OTM call with good liquidity
                calls_df = pd.DataFrame(calls)
                return self._find_directional_strike(spot_price, calls_df, 'CE', direction)
            
            elif direction == 'bearish' and puts:
                # Find ATM or slightly OTM put with good liquidity
                puts_df = pd.DataFrame(puts)
                return self._find_directional_strike(spot_price, puts_df, 'PE', direction)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding optimal buying strikes: {str(e)}")
            return None
    
    def _find_strangle_strikes(self, spot_price: float, calls_df: pd.DataFrame, 
                             puts_df: pd.DataFrame, volatility: float) -> Optional[Dict]:
        """Find optimal strikes for short strangle"""
        try:
            # Target strikes based on expected move
            expected_move = spot_price * (volatility / 100) * np.sqrt(30/365)  # 30-day expected move
            
            # Call strike: slightly OTM
            call_target = spot_price + (expected_move * 0.7)
            call_strike = self._find_nearest_liquid_strike(calls_df, call_target)
            
            # Put strike: slightly OTM
            put_target = spot_price - (expected_move * 0.7)
            put_strike = self._find_nearest_liquid_strike(puts_df, put_target)
            
            if call_strike and put_strike:
                # Calculate expected premium and risk
                call_premium = call_strike.get('lastPrice', 0)
                put_premium = put_strike.get('lastPrice', 0)
                
                total_premium = call_premium + put_premium
                max_profit = total_premium
                
                # Max loss is theoretically unlimited, but calculate for first standard deviation
                max_loss = max(
                    call_strike['strike'] - spot_price - total_premium,
                    spot_price - put_strike['strike'] - total_premium
                )
                
                confidence = self._calculate_strangle_confidence(
                    spot_price, call_strike['strike'], put_strike['strike'], 
                    volatility, total_premium
                )
                
                return {
                    'call_strike': call_strike['strike'],
                    'put_strike': put_strike['strike'],
                    'call_premium': call_premium,
                    'put_premium': put_premium,
                    'total_premium': total_premium,
                    'max_profit': max_profit,
                    'max_loss': max_loss,
                    'confidence': confidence
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding strangle strikes: {str(e)}")
            return None
    
    def _find_iron_condor_strikes(self, spot_price: float, calls_df: pd.DataFrame, 
                                puts_df: pd.DataFrame) -> Optional[Dict]:
        """Find optimal strikes for iron condor"""
        try:
            # Iron condor: sell ATM strangle, buy OTM protection
            
            # Short strikes (inner)
            short_call = self._find_nearest_liquid_strike(calls_df, spot_price * 1.02)
            short_put = self._find_nearest_liquid_strike(puts_df, spot_price * 0.98)
            
            # Long strikes (outer) - protection
            long_call = self._find_nearest_liquid_strike(calls_df, spot_price * 1.05)
            long_put = self._find_nearest_liquid_strike(puts_df, spot_price * 0.95)
            
            if all([short_call, short_put, long_call, long_put]):
                # Calculate net premium received
                premium_received = (short_call.get('lastPrice', 0) + 
                                 short_put.get('lastPrice', 0))
                premium_paid = (long_call.get('lastPrice', 0) + 
                              long_put.get('lastPrice', 0))
                
                net_premium = premium_received - premium_paid
                
                # Max profit is net premium received
                max_profit = net_premium
                
                # Max loss is width of strikes minus net premium
                call_width = long_call['strike'] - short_call['strike']
                put_width = short_put['strike'] - long_put['strike']
                max_loss = max(call_width, put_width) - net_premium
                
                legs = [
                    {'option_type': 'CE', 'strike': short_call['strike'], 'action': 'SELL'},
                    {'option_type': 'PE', 'strike': short_put['strike'], 'action': 'SELL'},
                    {'option_type': 'CE', 'strike': long_call['strike'], 'action': 'BUY'},
                    {'option_type': 'PE', 'strike': long_put['strike'], 'action': 'BUY'}
                ]
                
                confidence = self._calculate_iron_condor_confidence(
                    spot_price, short_call['strike'], short_put['strike'], net_premium
                )
                
                return {
                    'legs': legs,
                    'net_premium': net_premium,
                    'max_profit': max_profit,
                    'max_loss': max_loss,
                    'confidence': confidence
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding iron condor strikes: {str(e)}")
            return None
    
    def _find_directional_strike(self, spot_price: float, options_df: pd.DataFrame, 
                               option_type: str, direction: str) -> Optional[Dict]:
        """Find optimal strike for directional options buying"""
        try:
            # Filter options with good liquidity
            liquid_options = options_df[
                (options_df.get('volume', 0) > 10) | 
                (options_df.get('openInterest', 0) > 50)
            ]
            
            if liquid_options.empty:
                liquid_options = options_df  # Fallback to all options
            
            # Find ATM or slightly OTM options
            if direction == 'bullish':
                # For calls, find slightly OTM
                target_range = (spot_price * 1.00, spot_price * 1.03)
            else:
                # For puts, find slightly OTM
                target_range = (spot_price * 0.97, spot_price * 1.00)
            
            suitable_options = liquid_options[
                (liquid_options['strike'] >= target_range[0]) & 
                (liquid_options['strike'] <= target_range[1])
            ]
            
            if not suitable_options.empty:
                # Select option with best risk-reward (highest delta per unit of price)
                best_option = suitable_options.iloc[0]  # Simplified selection
                
                confidence = self._calculate_directional_confidence(
                    spot_price, best_option['strike'], direction, 
                    best_option.get('impliedVolatility', 20)
                )
                
                return {
                    'strike': best_option['strike'],
                    'premium': best_option.get('lastPrice', 0),
                    'confidence': confidence,
                    'delta': best_option.get('delta', 0.5),
                    'iv': best_option.get('impliedVolatility', 20)
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding directional strike: {str(e)}")
            return None
    
    def _find_nearest_liquid_strike(self, options_df: pd.DataFrame, target_price: float):
        """Find the nearest liquid strike to target price"""
        try:
            # Filter for liquid options
            liquid_options = options_df[
                ((options_df.get('volume', 0) > 10) | 
                 (options_df.get('openInterest', 0) > 50)) &
                (options_df.get('lastPrice', 0) > 0)
            ]
            
            if liquid_options.empty:
                # Fallback to options with non-zero price
                liquid_options = options_df[options_df.get('lastPrice', 0) > 0]
            
            if liquid_options.empty:
                return None
            
            # Find nearest strike
            liquid_options['distance'] = abs(liquid_options['strike'] - target_price)
            nearest = liquid_options.loc[liquid_options['distance'].idxmin()]
            
            return nearest.to_dict()
            
        except Exception as e:
            self.logger.error(f"Error finding nearest liquid strike: {str(e)}")
            return None
    
    def _calculate_strangle_confidence(self, spot_price: float, call_strike: float, 
                                     put_strike: float, volatility: float, 
                                     premium: float) -> float:
        """Calculate confidence score for strangle strategy"""
        try:
            # Factors that increase confidence:
            # 1. High volatility (more premium)
            # 2. Strikes well outside expected range
            # 3. Good premium collection
            
            # Expected move (1 standard deviation)
            expected_move = spot_price * (volatility / 100) * np.sqrt(30/365)
            
            # Distance from spot to strikes
            call_distance = (call_strike - spot_price) / spot_price
            put_distance = (spot_price - put_strike) / spot_price
            
            # Normalize distances
            call_score = min(call_distance / 0.05, 1.0)  # 5% OTM gives max score
            put_score = min(put_distance / 0.05, 1.0)
            
            # Volatility score (higher is better for selling)
            vol_score = min(volatility / 30, 1.0)  # 30% IV gives max score
            
            # Premium score (higher premium relative to spot price is better)
            premium_score = min((premium / spot_price) / 0.02, 1.0)  # 2% of spot gives max score
            
            # Combine scores
            confidence = (call_score + put_score + vol_score + premium_score) / 4
            
            return round(confidence, 2)
            
        except Exception as e:
            self.logger.error(f"Error calculating strangle confidence: {str(e)}")
            return 0.5
    
    def _calculate_iron_condor_confidence(self, spot_price: float, call_strike: float, 
                                        put_strike: float, net_premium: float) -> float:
        """Calculate confidence score for iron condor strategy"""
        try:
            # Iron condor works best in low volatility, range-bound markets
            
            # Distance from spot to short strikes
            call_distance = abs(call_strike - spot_price) / spot_price
            put_distance = abs(put_strike - spot_price) / spot_price
            
            # Prefer strikes close to spot (within 2-3%)
            distance_score = 1.0 - min((call_distance + put_distance) / 0.06, 1.0)
            
            # Premium score (positive net premium is essential)
            premium_score = 1.0 if net_premium > 0 else 0.0
            
            # Combine scores
            confidence = (distance_score + premium_score) / 2
            
            return round(confidence, 2)
            
        except Exception as e:
            self.logger.error(f"Error calculating iron condor confidence: {str(e)}")
            return 0.5
    
    def _calculate_directional_confidence(self, spot_price: float, strike: float, 
                                        direction: str, iv: float) -> float:
        """Calculate confidence score for directional options buying"""
        try:
            # Factors for options buying:
            # 1. Strike selection (ATM to slightly OTM)
            # 2. Lower IV is better for buying
            # 3. Time to expiry considerations
            
            # Strike score (prefer ATM to slightly OTM)
            moneyness = strike / spot_price
            
            if direction == 'bullish':
                # For calls, prefer 1.00 to 1.03
                if 1.00 <= moneyness <= 1.03:
                    strike_score = 1.0 - (moneyness - 1.00) / 0.03
                else:
                    strike_score = 0.5
            else:
                # For puts, prefer 0.97 to 1.00
                if 0.97 <= moneyness <= 1.00:
                    strike_score = 1.0 - (1.00 - moneyness) / 0.03
                else:
                    strike_score = 0.5
            
            # IV score (lower is better for buying)
            iv_score = max(0, 1.0 - (iv - 15) / 20)  # Prefer IV below 35%
            
            # Combine scores
            confidence = (strike_score + iv_score) / 2
            
            return round(confidence, 2)
            
        except Exception as e:
            self.logger.error(f"Error calculating directional confidence: {str(e)}")
            return 0.5