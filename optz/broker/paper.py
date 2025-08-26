from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime
import uuid

from .base import Broker, Order, Position


class PaperBroker(Broker):
	def __init__(self, starting_cash: float = 100000.0):
		self._cash = starting_cash
		self._positions: Dict[str, Position] = {}
		self._orders: Dict[str, Order] = {}

	def get_cash(self) -> float:
		return self._cash

	def place_market_order(self, symbol: str, qty: int, side: str, price: float, ts: datetime) -> Order:
		order_id = str(uuid.uuid4())
		cost = qty * price
		if side == "buy":
			self._cash -= cost
			pos = self._positions.get(symbol)
			if pos:
				new_qty = pos.qty + qty
				pos.avg_price = (pos.avg_price * pos.qty + cost) / max(new_qty, 1)
				pos.qty = new_qty
			else:
				self._positions[symbol] = Position(symbol=symbol, qty=qty, avg_price=price)
		elif side == "sell":
			pos = self._positions.get(symbol)
			if pos and pos.qty >= qty:
				self._cash += qty * price
				pos.qty -= qty
				if pos.qty == 0:
					self._positions.pop(symbol, None)
			else:
				self._cash += qty * price
		order = Order(order_id=order_id, symbol=symbol, qty=qty, side=side, price=price, ts=ts, status="filled")
		self._orders[order_id] = order
		return order

	def get_positions(self) -> Dict[str, Position]:
		return dict(self._positions)

	def close_position(self, symbol: str, price: float, ts: datetime) -> Optional[Order]:
		pos = self._positions.get(symbol)
		if not pos:
			return None
		return self.place_market_order(symbol, pos.qty, "sell", price, ts)