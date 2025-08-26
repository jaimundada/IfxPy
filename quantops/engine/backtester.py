from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

from ..utils.types import Candle, BacktestResult, Fill


@dataclass
class MarketState:
	index_symbol: str
	minute_index: int
	current_candle: Candle
	candles: List[Candle]
	equity: float


class Backtester:
	def __init__(self, provider, strategy, executor):
		self.provider = provider
		self.strategy = strategy
		self.executor = executor

	def run(self, start: datetime, end: datetime) -> BacktestResult:
		candles = self.provider.get_minute_candles(self.strategy.index_symbol, start, end)
		if not candles:
			return BacktestResult(equity_curve=[self.executor.cash_balance], trades=[])

		equity_curve: List[float] = []
		trades: List[Fill] = []

		for i, candle in enumerate(candles):
			state = MarketState(
				index_symbol=self.strategy.index_symbol,
				minute_index=i,
				current_candle=candle,
				candles=candles[: i + 1],
				equity=self.executor.total_equity(mark_to_market_price=candle.close),
			)
			orders = self.strategy.on_minute(state)
			for order in orders:
				fill = self.executor.execute(order, candle_time=candle.start, reference_price=candle.close)
				if fill is not None:
					trades.append(fill)

			equity_curve.append(self.executor.total_equity(mark_to_market_price=candle.close))

		return BacktestResult(equity_curve=equity_curve, trades=trades)