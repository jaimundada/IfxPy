from abc import ABC, abstractmethod
from typing import Iterable, Optional
import pandas as pd


class MarketDataProvider(ABC):
	@abstractmethod
	def get_history(self, symbol: str, start: str, end: str, interval: str = "1m") -> pd.DataFrame:
		"""Return historical OHLCV with DatetimeIndex in local timezone if possible."""
		raise NotImplementedError

	@abstractmethod
	def get_ltp(self, symbol: str) -> Optional[float]:
		"""Return last traded price if available."""
		raise NotImplementedError

	def stream_quotes(self, symbols: Iterable[str]):
		"""Optional: yield streaming quotes. Default raises NotImplementedError."""
		raise NotImplementedError("Streaming not implemented for this provider")