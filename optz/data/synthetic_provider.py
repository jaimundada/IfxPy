from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
import pandas as pd
import numpy as np

from .base import DataProvider
from ..utils.time import US_EASTERN


class SyntheticProvider(DataProvider):
	def __init__(self, seed: int = 42, start_price: float = 100.0):
		np.random.seed(seed)
		self.start_price = start_price

	def get_minute_ohlc(self, symbol: str, session_date: date) -> pd.DataFrame:
		start = datetime(session_date.year, session_date.month, session_date.day, 9, 30, tzinfo=US_EASTERN)
		end = datetime(session_date.year, session_date.month, session_date.day, 16, 0, tzinfo=US_EASTERN)
		minutes = int((end - start).total_seconds() // 60)
		idx = pd.date_range(start=start, periods=minutes + 1, freq="1min", tz=US_EASTERN)
		rets = np.random.normal(loc=0.0001, scale=0.002, size=len(idx))
		prices = [self.start_price]
		for r in rets[1:]:
			prices.append(prices[-1] * (1 + r))
		close = pd.Series(prices, index=idx)
		opn = close.shift(1).fillna(close.iloc[0])
		high = pd.concat([opn, close], axis=1).max(axis=1) * (1 + 0.0005)
		low = pd.concat([opn, close], axis=1).min(axis=1) * (1 - 0.0005)
		vol = pd.Series(np.random.randint(100, 1000, size=len(idx)), index=idx)
		df = pd.DataFrame({"open": opn, "high": high, "low": low, "close": close, "volume": vol})
		return df

	def get_last_price(self, symbol: str) -> float:
		return float(self.start_price)