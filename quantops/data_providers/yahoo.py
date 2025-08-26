from datetime import datetime, timezone
from typing import List, Optional
import time
import random
import requests

from ..utils.types import Candle


class YahooProvider:
	BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

	def __init__(self, session: Optional[requests.Session] = None, max_retries: int = 5) -> None:
		self.session = session or requests.Session()
		self.session.headers.update({
			"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
		})
		self.max_retries = max_retries

	@staticmethod
	def _to_unix(dt: datetime) -> int:
		if dt.tzinfo is None:
			dt = dt.replace(tzinfo=timezone.utc)
		return int(dt.timestamp())

	def get_minute_candles(self, symbol: str, start: datetime, end: datetime) -> List[Candle]:
		params = {
			"interval": "1m",
			"period1": self._to_unix(start),
			"period2": self._to_unix(end),
		}
		url = self.BASE_URL.format(symbol=symbol)
		retries = 0
		while True:
			r = self.session.get(url, params=params, timeout=20)
			if r.status_code == 200:
				break
			if r.status_code in (429, 502, 503, 504) and retries < self.max_retries:
				retries += 1
				delay = min(2 ** retries + random.uniform(0, 0.5), 10)
				time.sleep(delay)
				continue
			# fail-soft
			return []

		data = r.json()
		result = data.get("chart", {}).get("result")
		if not result:
			return []
		result = result[0]
		timestamps = result.get("timestamp", [])
		ind = result.get("indicators", {}).get("quote", [{}])[0]
		opens = ind.get("open", [])
		highs = ind.get("high", [])
		lows = ind.get("low", [])
		closes = ind.get("close", [])
		vols = ind.get("volume", [])
		candles: List[Candle] = []
		for i, ts in enumerate(timestamps):
			if ts is None:
				continue
			try:
				candles.append(
					Candle(
						start=datetime.fromtimestamp(ts, tz=timezone.utc).replace(tzinfo=None),
						open=float(opens[i]) if opens[i] is not None else float(closes[i]),
						high=float(highs[i]) if highs[i] is not None else float(closes[i]),
						low=float(lows[i]) if lows[i] is not None else float(closes[i]),
						close=float(closes[i]),
						volume=float(vols[i]) if i < len(vols) and vols[i] is not None else 0.0,
					)
				)
			except (IndexError, ValueError, TypeError):
				continue
		return candles