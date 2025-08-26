from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from ..utils.types import Order, Fill, Position


class PaperExecutor:
	def __init__(self, initial_cash: float = 100000.0) -> None:
		self.cash_balance: float = initial_cash
		self.symbol_to_position: Dict[str, Position] = {}

	def execute(self, order: Order, candle_time: datetime, reference_price: float) -> Optional[Fill]:
		fill_price = reference_price if order.price is None else order.price
		if order.order_type == "limit" and order.price is not None:
			# naive: only fill if price crosses
			if order.side == "buy" and fill_price < reference_price:
				return None
			if order.side == "sell" and fill_price > reference_price:
				return None

		cost = fill_price * order.qty
		if order.side == "buy":
			if self.cash_balance < cost:
				return None
			self.cash_balance -= cost
			pos = self.symbol_to_position.get(order.symbol)
			if pos is None:
				self.symbol_to_position[order.symbol] = Position(symbol=order.symbol, qty=order.qty, avg_price=fill_price)
			else:
				total_qty = pos.qty + order.qty
				pos.avg_price = (pos.avg_price * pos.qty + fill_price * order.qty) / max(total_qty, 1)
				pos.qty = total_qty
		else:  # sell
			pos = self.symbol_to_position.get(order.symbol)
			qty_to_sell = order.qty
			if pos is None or pos.qty < qty_to_sell:
				return None
			pos.qty -= qty_to_sell
			self.cash_balance += fill_price * qty_to_sell
			if pos.qty == 0:
				self.symbol_to_position.pop(order.symbol, None)

		return Fill(order=order, fill_price=fill_price, fill_time=candle_time)

	def total_equity(self, mark_to_market_price: float) -> float:
		equity = self.cash_balance
		for pos in self.symbol_to_position.values():
			equity += pos.qty * mark_to_market_price
		return equity