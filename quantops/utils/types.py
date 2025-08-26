from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class Candle:
	start: datetime
	open: float
	high: float
	low: float
	close: float
	volume: float = 0.0


@dataclass
class Order:
	symbol: str
	qty: int
	side: str  # buy/sell
	price: Optional[float] = None
	order_type: str = "market"
	placed_at: Optional[datetime] = None


@dataclass
class Fill:
	order: Order
	fill_price: float
	fill_time: datetime


@dataclass
class Position:
	symbol: str
	qty: int
	avg_price: float


@dataclass
class BacktestResult:
	equity_curve: List[float]
	trades: List[Fill]

	def summary(self) -> str:
		return f"Trades: {len(self.trades)}, Final Equity: {self.equity_curve[-1]:.2f}" if self.equity_curve else "No data"