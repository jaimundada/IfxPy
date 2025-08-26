from __future__ import annotations
import pandas as pd
import yfinance as yf
from typing import Optional
from .base import MarketDataProvider


class YahooFinanceProvider(MarketDataProvider):
	def get_history(self, symbol: str, start: str, end: str, interval: str = "1m") -> pd.DataFrame:
		data = yf.download(tickers=symbol, start=start, end=end, interval=interval, auto_adjust=False, progress=False)
		if not isinstance(data, pd.DataFrame) or data.empty:
			return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])  # empty
		# Normalize columns
		data = data.rename(columns={"Adj Close": "AdjClose"})
		data.index = pd.to_datetime(data.index)
		data = data[["Open", "High", "Low", "Close", "Volume"]]
		data.dropna(how="any", inplace=True)
		return data

	def get_ltp(self, symbol: str) -> Optional[float]:
		info = yf.Ticker(symbol)
		price = None
		try:
			price = info.fast_info.get("last_price")
		except Exception:
			pass
		if price is None:
			try:
				px = info.history(period="1d", interval="1m")
				if not px.empty:
					price = float(px["Close"].iloc[-1])
			except Exception:
				return None
		return float(price) if price is not None else None