from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import pandas as pd


@dataclass
class Signal:
	action: str  # "buy_call", "buy_put", "flat"
	strike: Optional[float]
	reason: str


class BaseStrategy(ABC):
	@abstractmethod
	def generate_signals(self, ohlcv: pd.DataFrame) -> Signal:
		"""Given minute OHLCV including the latest bar, return a trading signal."""
		raise NotImplementedError