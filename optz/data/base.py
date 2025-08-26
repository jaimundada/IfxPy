from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import Protocol, Optional
import pandas as pd


class DataProvider(ABC):
    @abstractmethod
    def get_minute_ohlc(self, symbol: str, session_date: date) -> pd.DataFrame:
        """Return a DataFrame with minute OHLCV for the session_date in local market tz.
        Required columns: [open, high, low, close, volume]; index must be tz-aware datetime.
        """
        raise NotImplementedError

    @abstractmethod
    def get_last_price(self, symbol: str) -> float:
        """Return the latest traded/close price."""
        raise NotImplementedError