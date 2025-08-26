from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict
import pandas as pd

from ..selection.strikes import round_to_atm_strike
from ..pricing.black_scholes import black_scholes_call, black_scholes_put


@dataclass
class MomentumATMConfig:
	assumed_iv: float = 0.20
	sl_pct: float = 0.30
	tp_pct: float = 0.50
	ma_fast: int = 9
	ma_slow: int = 21
	strike_step: float = 1.0
	contract_multiplier: int = 100
	risk_free_rate: float = 0.01


class MomentumATMStrategy:
	def __init__(self, config: MomentumATMConfig):
		self.cfg = config

	def _calc_ma(self, prices: pd.Series, length: int) -> pd.Series:
		return prices.rolling(window=length, min_periods=1).mean()

	def generate_signals(self, ohlc: pd.DataFrame) -> pd.Series:
		close = ohlc["close"]
		ma_fast = self._calc_ma(close, self.cfg.ma_fast)
		ma_slow = self._calc_ma(close, self.cfg.ma_slow)
		signal = (ma_fast > ma_slow).astype(int) - (ma_fast < ma_slow).astype(int)
		return signal  # +1 bull, -1 bear, 0 flat

	def price_option(self, spot: float, strike: float, minutes_to_expiry: int, option_type: str) -> float:
		T = max(minutes_to_expiry, 1) / (365.0 * 24.0 * 60.0)
		if option_type == "call":
			return black_scholes_call(spot, strike, T, self.cfg.risk_free_rate, self.cfg.assumed_iv)
		else:
			return black_scholes_put(spot, strike, T, self.cfg.risk_free_rate, self.cfg.assumed_iv)

	def decide_trade(self, ts: datetime, spot: float, signal: int) -> Optional[Dict]:
		if signal == 0:
			return None
		strike = round_to_atm_strike(spot, self.cfg.strike_step)
		minutes_to_expiry = 390  # assume same-day like weekly for demo
		if signal > 0:
			option_type = "call"
		else:
			option_type = "put"
		prem = self.price_option(spot, strike, minutes_to_expiry, option_type)
		qty = 1
		return {
			"symbol": f"{option_type.upper()}_{int(strike)}",
			"qty": qty,
			"side": "buy",
			"entry_price": prem,
			"sl": prem * (1 - self.cfg.sl_pct),
			"tp": prem * (1 + self.cfg.tp_pct),
			"multiplier": self.cfg.contract_multiplier,
		}

	def update_position(self, pos: Dict, spot: float, ts: datetime) -> Dict:
		strike = float(pos["symbol"].split("_")[1])
		option_type = "call" if pos["symbol"].startswith("CALL") else "put"
		minutes_left = max(1, 390 - ts.hour * 60 - ts.minute)
		prem = self.price_option(spot, strike, minutes_left, option_type)
		pos["last_price"] = prem
		pos["pnl"] = (prem - pos["entry_price"]) * pos["qty"] * pos["multiplier"]
		pos["exit"] = None
		if prem <= pos["sl"] or prem >= pos["tp"]:
			pos["exit"] = "exit"
		return pos