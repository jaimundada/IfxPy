import time
from datetime import datetime, timedelta
from typing import Optional

from .execution import PaperExecutor


class LiveEngine:
	def __init__(self, provider, strategy, executor: Optional[PaperExecutor] = None):
		self.provider = provider
		self.strategy = strategy
		executor = executor or PaperExecutor()
		self.executor = executor
		self._running = True

	def run(self):
		# Very naive live loop: poll the last 1 hour, every 60s
		while self._running:
			end = datetime.utcnow()
			start = end - timedelta(hours=1)
			candles = self.provider.get_minute_candles(self.strategy.index_symbol, start, end)
			if candles:
				state = type("State", (), {})()
				setattr(state, "index_symbol", self.strategy.index_symbol)
				setattr(state, "minute_index", len(candles) - 1)
				setattr(state, "current_candle", candles[-1])
				setattr(state, "candles", candles)
				setattr(state, "equity", self.executor.total_equity(mark_to_market_price=candles[-1].close))
				for order in self.strategy.on_minute(state):
					self.executor.execute(order, candle_time=candles[-1].start, reference_price=candles[-1].close)
			time.sleep(60)