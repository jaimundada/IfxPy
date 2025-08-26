from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from .base import Broker, Order, Position


class DhanBroker(Broker):
	"""Stub Dhan connector.
	Replace methods with actual HTTP calls and session management.
	"""

	def __init__(self, api_key: str = "", access_token: str = ""):
		self.api_key = api_key
		self.access_token = access_token

	def get_cash(self) -> float:
		raise NotImplementedError("Dhan connector not implemented. Provide credentials and implement.")

	def place_market_order(self, symbol: str, qty: int, side: str, price: float, ts: datetime) -> Order:
		raise NotImplementedError("Dhan connector not implemented.")

	def get_positions(self) -> Dict[str, Position]:
		raise NotImplementedError("Dhan connector not implemented.")

	def close_position(self, symbol: str, price: float, ts: datetime) -> Optional[Order]:
		raise NotImplementedError("Dhan connector not implemented.")