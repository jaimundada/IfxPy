from __future__ import annotations

import time
from datetime import datetime
from typing import Dict

from ..data.base import DataProvider
from ..broker.base import Broker
from ..strategy.momentum_atm import MomentumATMStrategy


class LiveRunner:
	def __init__(self, provider: DataProvider, broker: Broker, strategy: MomentumATMStrategy):
		self.provider = provider
		self.broker = broker
		self.strategy = strategy

	def run(self, symbol: str):
		open_position: Dict | None = None
		while True:
			px = self.provider.get_last_price(symbol)
			ts = datetime.utcnow()
			signal = 1 if int(ts.minute) % 10 < 5 else -1  # placeholder: alternate for demo
			if open_position:
				pos = self.strategy.update_position(open_position, px, ts)
				if pos.get("exit"):
					self.broker.close_position(pos["symbol"], pos["last_price"], ts)
					open_position = None
			elif signal != 0:
				decision = self.strategy.decide_trade(ts, px, signal)
				if decision:
					self.broker.place_market_order(decision["symbol"], decision["qty"], decision["side"], decision["entry_price"], ts)
					open_position = decision
			time.sleep(60)