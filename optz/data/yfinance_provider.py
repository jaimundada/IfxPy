from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
import pandas as pd
import yfinance as yf

from .base import DataProvider
from ..utils.time import US_EASTERN


class YFinanceProvider(DataProvider):
	def get_minute_ohlc(self, symbol: str, session_date: date) -> pd.DataFrame:
		start = datetime(session_date.year, session_date.month, session_date.day, 0, 0, tzinfo=US_EASTERN)
		end = start + timedelta(days=1)
		tkr = yf.Ticker(symbol)
		df = tkr.history(interval="1m", start=start.astimezone(ZoneInfo("UTC")), end=end.astimezone(ZoneInfo("UTC")))
		if df.empty:
			# Fallback: fetch last 30d of 1m data and filter by session date
			df = tkr.history(interval="1m", period="30d")
			if df.empty:
				return pd.DataFrame(columns=["open", "high", "low", "close", "volume"]).set_index(pd.DatetimeIndex([], tz=US_EASTERN))
		df.index = df.index.tz_convert(US_EASTERN)
		df = df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
		# Filter to the requested session date bounds
		mask = (df.index >= start) & (df.index < end)
		df = df.loc[mask]
		return df[["open", "high", "low", "close", "volume"]]

	def get_last_price(self, symbol: str) -> float:
		tkr = yf.Ticker(symbol)
		px = tkr.history(period="1d")
		if px.empty:
			return float("nan")
		return float(px["Close"].iloc[-1])