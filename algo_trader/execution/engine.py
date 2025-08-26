from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import math

from ..brokers.base import Broker, Order, OrderFill


@dataclass
class RiskConfig:
	capital: float
	risk_per_trade: float = 0.01
	multiplier: int = 50  # lot size approximation for NIFTY-like options


@dataclass
class PositionState:
	is_open: bool = False
	side: Optional[str] = None  # "call" or "put"
	entry_price: float = 0.0
	quantity: int = 0
	target_price: float = 0.0
	stop_price: float = 0.0
	description: str = ""


class ExecutionEngine:
	def __init__(self, broker: Broker, risk: RiskConfig):
		self.broker = broker
		self.risk = risk
		self.position = PositionState()

	def _compute_qty(self, entry_price: float, sl_price: float) -> int:
		per_unit_risk = max(entry_price - sl_price, sl_price - entry_price)
		per_contract_risk = per_unit_risk * self.risk.multiplier
		if per_contract_risk <= 0:
			return 0
		qty = math.floor((self.risk.capital * self.risk.risk_per_trade) / per_contract_risk)
		return max(qty, 0)

	def maybe_enter(self, option_side: str, option_price: float) -> Optional[OrderFill]:
		if self.position.is_open:
			return None
		# define target/sl
		target_price = option_price * 1.2
		stop_price = option_price * 0.9
		qty = self._compute_qty(option_price, stop_price)
		if qty <= 0:
			return None
		fill = self.broker.place_order(Order(symbol=f"OPT-{option_side}", side="buy", quantity=qty, order_type="market", price=option_price))
		self.position = PositionState(
			is_open=True,
			side=option_side,
			entry_price=option_price,
			quantity=qty,
			target_price=target_price,
			stop_price=stop_price,
			description="entry"
		)
		return fill

	def maybe_exit(self, option_price: float) -> Optional[OrderFill]:
		if not self.position.is_open:
			return None
		if option_price >= self.position.target_price or option_price <= self.position.stop_price:
			fill = self.broker.place_order(Order(symbol=f"OPT-{self.position.side}", side="sell", quantity=self.position.quantity, order_type="market", price=option_price))
			self.position = PositionState()
			return fill
		return None