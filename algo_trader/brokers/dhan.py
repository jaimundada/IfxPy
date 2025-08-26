from __future__ import annotations
import os
from .base import Broker, Order, OrderFill


class DhanBroker(Broker):
	def __init__(self):
		self.access_token = os.getenv("DHAN_ACCESS_TOKEN", "")
		# TODO: Implement Dhan API endpoints for orders and positions

	def place_order(self, order: Order) -> OrderFill:
		return OrderFill(order_id="sim-dhan", avg_price=order.price or 0.0, filled_qty=order.quantity, status="filled")

	def cancel_order(self, order_id: str) -> bool:
		return True

	def get_positions(self) -> list[dict]:
		return []