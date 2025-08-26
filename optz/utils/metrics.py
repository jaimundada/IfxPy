from __future__ import annotations

from typing import Dict, List
import math


def compute_metrics(equity_curve: List[float]) -> Dict[str, float]:
    if not equity_curve:
        return {"final": 0.0, "max_drawdown": 0.0, "sharpe": 0.0}
    returns = []
    peak = equity_curve[0]
    max_dd = 0.0
    for i in range(1, len(equity_curve)):
        prev = equity_curve[i - 1]
        cur = equity_curve[i]
        if prev != 0:
            returns.append((cur - prev) / prev)
        peak = max(peak, cur)
        dd = (peak - cur) / peak if peak != 0 else 0.0
        max_dd = max(max_dd, dd)
    mean_ret = sum(returns) / len(returns) if returns else 0.0
    std_ret = math.sqrt(
        sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1)
    ) if len(returns) > 1 else 0.0
    sharpe = (mean_ret / std_ret * math.sqrt(252 * 6.5 * 60)) if std_ret != 0 else 0.0
    return {"final": equity_curve[-1], "max_drawdown": max_dd, "sharpe": sharpe}