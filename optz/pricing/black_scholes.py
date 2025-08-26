from __future__ import annotations

import math
from typing import Dict

try:
	from scipy.stats import norm  # type: ignore
except Exception:
	class _Norm:
		@staticmethod
		def cdf(x: float) -> float:
			return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
		@staticmethod
		def pdf(x: float) -> float:
			return (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * x * x)
	norm = _Norm()


def _d1(S: float, K: float, T: float, r: float, sigma: float) -> float:
    return (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))


def _d2(d1: float, sigma: float, T: float) -> float:
    return d1 - sigma * math.sqrt(T)


def black_scholes_call(S: float, K: float, T: float, r: float, sigma: float) -> float:
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return max(0.0, S - K)
    d1 = _d1(S, K, T, r, sigma)
    d2 = _d2(d1, sigma, T)
    return S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)


def black_scholes_put(S: float, K: float, T: float, r: float, sigma: float) -> float:
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return max(0.0, K - S)
    d1 = _d1(S, K, T, r, sigma)
    d2 = _d2(d1, sigma, T)
    return K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)


def compute_greeks(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> Dict[str, float]:
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return {"delta": 0.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0}
    d1 = _d1(S, K, T, r, sigma)
    d2 = _d2(d1, sigma, T)
    pdf = norm.pdf(d1)
    if option_type.lower() == "call":
        delta = norm.cdf(d1)
        theta = (
            -(S * pdf * sigma) / (2 * math.sqrt(T))
            - r * K * math.exp(-r * T) * norm.cdf(d2)
        )
    else:
        delta = -norm.cdf(-d1)
        theta = (
            -(S * pdf * sigma) / (2 * math.sqrt(T))
            + r * K * math.exp(-r * T) * norm.cdf(-d2)
        )
    gamma = pdf / (S * sigma * math.sqrt(T))
    vega = S * pdf * math.sqrt(T)
    return {"delta": float(delta), "gamma": float(gamma), "theta": float(theta), "vega": float(vega)}