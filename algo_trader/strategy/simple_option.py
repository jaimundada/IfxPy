from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd

from .base import BaseStrategy, Signal
from ..options.pricing import select_atm_strike


@dataclass
class SimpleOptionConfig:
	lookback: int = 20
	strike_step: float = 50.0
	target_pct: float = 0.2
	sl_pct: float = 0.1


class SimpleOptionStrategy(BaseStrategy):
	def __init__(self, config: Optional[SimpleOptionConfig] = None):
		self.config = config or SimpleOptionConfig()

	def generate_signals(self, ohlcv: pd.DataFrame) -> Signal:
		if len(ohlcv) < max(5, self.config.lookback + 1):
			return Signal(action="flat", strike=None, reason="insufficient data")
		recent = ohlcv.tail(self.config.lookback + 1)
		prev = recent.iloc[:-1]
		last = recent.iloc[-1]
		prev_high = float(prev["High"].max())
		prev_low = float(prev["Low"].min())
		close = float(last["Close"]) if "Close" in last else float(last.close)
		strike = select_atm_strike(close, self.config.strike_step)
		if close > prev_high:
			return Signal(action="buy_call", strike=strike, reason="breakout_up")
		if close < prev_low:
			return Signal(action="buy_put", strike=strike, reason="breakdown_down")
		return Signal(action="flat", strike=None, reason="no_signal")