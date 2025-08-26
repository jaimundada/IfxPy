from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, Optional


OrderSide = Literal["buy", "sell"]
OrderType = Literal["market", "limit"]


@dataclass
class Order:
	symbol: str
	side: OrderSide
	quantity: int
	order_type: OrderType = "market"
	price: Optional[float] = None
	client_order_id: Optional[str] = None


@dataclass
class OrderFill:
	order_id: str
	avg_price: float
	filled_qty: int
	status: Literal["filled", "partial", "rejected"]


class Broker(ABC):
	@abstractmethod
	def place_order(self, order: Order) -> OrderFill:
		...

	@abstractmethod
	def cancel_order(self, order_id: str) -> bool:
		...

	@abstractmethod
	def get_positions(self) -> list[dict]:
		...