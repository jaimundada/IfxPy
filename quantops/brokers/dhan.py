from typing import Optional
from dataclasses import dataclass

from ..utils.types import Order, Fill


@dataclass
class DhanCredentials:
	client_id: str
	access_token: str


class DhanBroker:
	def __init__(self, creds: Optional[DhanCredentials] = None) -> None:
		self.creds = creds
		self.session = None

	def login(self) -> None:
		# TODO: Implement Dhan API auth
		raise NotImplementedError("DhanBroker.login requires Dhan API integration")

	def place_order(self, order: Order) -> Optional[Fill]:
		# TODO: Map Order to Dhan order params and place via API
		raise NotImplementedError("DhanBroker.place_order not implemented")

	def cancel_order(self, order_id: str) -> bool:
		# TODO: Cancel order via API
		raise NotImplementedError("DhanBroker.cancel_order not implemented")