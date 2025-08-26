from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, Any, Optional
import pandas as pd

from ..data.base import DataProvider
from ..broker.base import Broker
from ..strategy.momentum_atm import MomentumATMStrategy
from ..utils.metrics import compute_metrics


@dataclass
class BacktestResult:
	final_equity: float
	max_drawdown: float
	sharpe: float
	trades: int


class BacktestEngine:
	def __init__(self, provider: DataProvider, broker: Broker, strategy: MomentumATMStrategy):
		self.provider = provider
		self.broker = broker
		self.strategy = strategy

	def run_session(self, symbol: str, session_date: Optional[date]) -> Dict[str, Any]:
		if session_date is None:
			raise ValueError("session_date is required for backtest")
		df = self.provider.get_minute_ohlc(symbol, session_date)
		if df.empty:
			return {"error": "No data"}
		signals = self.strategy.generate_signals(df)
		positions: Dict[str, dict] = {}
		equity_curve = [self.broker.get_cash()]
		trades = 0
		for ts, row in df.iterrows():
			spot = float(row["close"])
			signal = int(signals.loc[ts])
			# Update open positions
			for sym, pos in list(positions.items()):
				pos = self.strategy.update_position(pos, spot, ts)
				if pos.get("exit"):
					# close
					self.broker.place_market_order(sym, pos["qty"], "sell", pos["last_price"], ts)
					positions.pop(sym, None)
					trades += 1
			# Entry logic: only if flat
			if not positions and signal != 0:
				decision = self.strategy.decide_trade(ts, spot, signal)
				if decision:
					sym = decision["symbol"]
					self.broker.place_market_order(sym, decision["qty"], decision["side"], decision["entry_price"], ts)
					positions[sym] = decision
					trades += 1
			# Compute equity
			total = self.broker.get_cash()
			for sym, pos in positions.items():
				last_price = pos.get("last_price", pos["entry_price"])  # approx
				total += last_price * pos["qty"] * pos["multiplier"]
			equity_curve.append(total)
		metrics = compute_metrics(equity_curve)
		return {
			"symbol": symbol,
			"date": session_date,
			"final_equity": metrics["final"],
			"max_drawdown": metrics["max_drawdown"],
			"sharpe": metrics["sharpe"],
			"trades": trades,
		}