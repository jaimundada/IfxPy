from __future__ import annotations

import math


def round_to_atm_strike(spot: float, step: float) -> float:
	if step <= 0:
		return float(round(spot))
	return round(spot / step) * step