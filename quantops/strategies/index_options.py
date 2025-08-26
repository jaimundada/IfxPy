from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ..utils.types import Order


@dataclass
class RiskConfig:
	stop_loss_pct: float = 0.01
	target_pct: float = 0.02
	day_max_loss_pct: float = 0.03
	unit_qty: int = 1


class IndexOptionsStrategy:
	def __init__(self, index_symbol: str, risk: RiskConfig | None = None) -> None:
		self.index_symbol = index_symbol
		self.risk = risk or RiskConfig()
		self.entry_price: float | None = None
		self.position_side: str | None = None  # "long" or "short"
		self.day_start_equity: float | None = None

	def on_minute(self, state) -> List[Order]:
		orders: List[Order] = []
		close_prices = [c.close for c in state.candles]
		if len(close_prices) < 6:
			return orders

		if self.day_start_equity is None:
			self.day_start_equity = state.equity

		ret5 = (close_prices[-1] - close_prices[-6]) / close_prices[-6]
		momentum = 1 if ret5 > 0 else (-1 if ret5 < 0 else 0)

		if self.entry_price is not None and self.position_side is not None:
			pnl_pct = (close_prices[-1] - self.entry_price) / self.entry_price if self.position_side == "long" else (self.entry_price - close_prices[-1]) / self.entry_price
			if pnl_pct <= -self.risk.stop_loss_pct or pnl_pct >= self.risk.target_pct:
				orders.append(Order(symbol=self.index_symbol, qty=self.risk.unit_qty, side="sell" if self.position_side == "long" else "buy"))
				self.entry_price = None
				self.position_side = None
				return orders

		if self.day_start_equity is not None:
			dd_pct = (state.equity - self.day_start_equity) / self.day_start_equity
			if dd_pct <= -self.risk.day_max_loss_pct:
				return orders

		if self.entry_price is None:
			if momentum > 0:
				orders.append(Order(symbol=self.index_symbol, qty=self.risk.unit_qty, side="buy"))
				self.entry_price = close_prices[-1]
				self.position_side = "long"
			elif momentum < 0:
				orders.append(Order(symbol=self.index_symbol, qty=self.risk.unit_qty, side="sell"))
				self.entry_price = close_prices[-1]
				self.position_side = "short"

		return orders