from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class Order:
	order_id: str
	symbol: str
	qty: int
	side: str  # "buy" or "sell"
	price: float
	ts: datetime
	status: str = "filled"


@dataclass
class Position:
	symbol: str
	qty: int
	avg_price: float
	unrealized_pnl: float = 0.0


class Broker:
	def get_cash(self) -> float:
		raise NotImplementedError

	def place_market_order(self, symbol: str, qty: int, side: str, price: float, ts: datetime) -> Order:
		raise NotImplementedError

	def get_positions(self) -> Dict[str, Position]:
		raise NotImplementedError

	def close_position(self, symbol: str, price: float, ts: datetime) -> Optional[Order]:
		raise NotImplementedError