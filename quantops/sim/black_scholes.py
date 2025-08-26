from math import log, sqrt, exp, erf
from typing import Literal, Optional


def _norm_cdf(x: float) -> float:
	return 0.5 * (1.0 + erf(x / sqrt(2.0)))


def _norm_pdf(x: float) -> float:
	return (1.0 / sqrt(2.0 * 3.141592653589793)) * exp(-0.5 * x * x)


def black_scholes_price(spot: float, strike: float, time_years: float, rate: float, vol: float, kind: Literal["call", "put"]) -> float:
	if time_years <= 0 or vol <= 0 or spot <= 0 or strike <= 0:
		return max(0.0, spot - strike) if kind == "call" else max(0.0, strike - spot)
	d1 = (log(spot / strike) + (rate + 0.5 * vol * vol) * time_years) / (vol * sqrt(time_years))
	d2 = d1 - vol * sqrt(time_years)
	if kind == "call":
		return spot * _norm_cdf(d1) - strike * exp(-rate * time_years) * _norm_cdf(d2)
	else:
		return strike * exp(-rate * time_years) * _norm_cdf(-d2) - spot * _norm_cdf(-d1)


def implied_volatility(target_price: float, spot: float, strike: float, time_years: float, rate: float, kind: Literal["call", "put"], initial_vol: float = 0.2) -> Optional[float]:
	vol = max(1e-4, initial_vol)
	for _ in range(50):
		price = black_scholes_price(spot, strike, time_years, rate, vol, kind)
		diff = price - target_price
		if abs(diff) < 1e-6:
			return vol
		if time_years <= 0:
			return None
		d1 = (log(spot / strike) + (rate + 0.5 * vol * vol) * time_years) / (vol * sqrt(time_years))
		vega = spot * _norm_pdf(d1) * sqrt(time_years)
		if vega < 1e-8:
			break
		vol = min(max(vol - diff / vega, 1e-4), 5.0)
	return None