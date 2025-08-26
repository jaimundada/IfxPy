from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict
import pandas as pd

from ..data_providers.base import MarketDataProvider
from ..data_providers.yfinance_provider import YahooFinanceProvider
from ..strategy.simple_option import SimpleOptionStrategy, SimpleOptionConfig
from ..execution.engine import ExecutionEngine, RiskConfig
from ..brokers.base import Broker, Order, OrderFill


class SimBroker(Broker):
	def __init__(self):
		self.trades: List[Dict] = []

	def place_order(self, order: Order) -> OrderFill:
		fill = OrderFill(order_id=f"sim-{len(self.trades)+1}", avg_price=order.price or 0.0, filled_qty=order.quantity, status="filled")
		self.trades.append({"id": fill.order_id, "side": order.side, "qty": order.quantity, "price": fill.avg_price})
		return fill

	def cancel_order(self, order_id: str) -> bool:
		return True

	def get_positions(self) -> list[dict]:
		return []


@dataclass
class BacktestResult:
	trades: pd.DataFrame
	summary: Dict[str, float]
	equity_curve: pd.Series


class Backtester:
	def __init__(self, provider: MarketDataProvider | None = None):
		self.provider = provider or YahooFinanceProvider()

	def run(self, symbol: str, start: str, end: str, capital: float = 200000.0, risk_per_trade: float = 0.01, interval: str = "1m") -> BacktestResult:
		bars = self.provider.get_history(symbol, start, end, interval=interval)
		if bars.empty:
			return BacktestResult(trades=pd.DataFrame(), summary={"trades": 0}, equity_curve=pd.Series(dtype=float))
		strategy = SimpleOptionStrategy(SimpleOptionConfig())
		broker = SimBroker()
		exec_engine = ExecutionEngine(broker, RiskConfig(capital=capital, risk_per_trade=risk_per_trade))
		rows = []
		equity = capital
		equity_curve = []
		for idx in range(len(bars)):
			window = bars.iloc[: idx + 1]
			signal = strategy.generate_signals(window)
			last_close = float(window.iloc[-1]["Close"])
			option_price = max(last_close * 0.03, 5.0)
			if signal.action == "buy_call":
				fill = exec_engine.maybe_enter("call", option_price)
				if fill:
					rows.append({"time": window.index[-1], "action": "buy_call", "price": float(fill.avg_price), "qty": int(fill.filled_qty)})
			elif signal.action == "buy_put":
				fill = exec_engine.maybe_enter("put", option_price)
				if fill:
					rows.append({"time": window.index[-1], "action": "buy_put", "price": float(fill.avg_price), "qty": int(fill.filled_qty)})
			# exits
			if exec_engine.position.is_open:
				entry_px = float(exec_engine.position.entry_price)
				exit_fill = exec_engine.maybe_exit(option_price)
				if exit_fill:
					pnl = (float(exit_fill.avg_price) - entry_px) * (exec_engine.risk.multiplier * int(exit_fill.filled_qty))
					rows.append({"time": window.index[-1], "action": "exit", "price": float(exit_fill.avg_price), "qty": int(exit_fill.filled_qty), "pnl": float(pnl)})
					equity += pnl
			equity_curve.append(equity)
		trades_df = pd.DataFrame(rows)
		if not trades_df.empty and "pnl" in trades_df:
			pnl_sum = float(trades_df["pnl"].fillna(0).sum())
		else:
			pnl_sum = 0.0
		summary = {"trades": int((trades_df[trades_df["action"] != "exit"].shape[0]) or 0), "net_pnl": pnl_sum, "ending_equity": equity}
		return BacktestResult(trades=trades_df, summary=summary, equity_curve=pd.Series(equity_curve, index=bars.index))