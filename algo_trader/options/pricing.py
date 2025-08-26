from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Literal
from scipy.stats import norm


@dataclass
class OptionQuote:
	underlying_price: float
	strike: float
	risk_free_rate: float
	volatility: float
	time_to_expiry_years: float
	type: Literal["call", "put"]


def black_scholes_price(params: OptionQuote) -> float:
	S = params.underlying_price
	K = params.strike
	r = params.risk_free_rate
	sigma = max(params.volatility, 1e-8)
	T = max(params.time_to_expiry_years, 1e-8)
	type_ = params.type
	d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
	d2 = d1 - sigma * math.sqrt(T)
	if type_ == "call":
		price = S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
	else:
		price = K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
	return float(price)


def select_atm_strike(underlying_price: float, strike_step: float) -> float:
	"""Round to nearest strike grid step."""
	return round(underlying_price / strike_step) * strike_step