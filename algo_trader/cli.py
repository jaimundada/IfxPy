from __future__ import annotations
import argparse
from datetime import datetime, timedelta
import time
from tabulate import tabulate

from .data_providers.yfinance_provider import YahooFinanceProvider
from .backtest.engine import Backtester
from .strategy.simple_option import SimpleOptionStrategy, SimpleOptionConfig
from .execution.engine import ExecutionEngine, RiskConfig
from .brokers.angel import AngelOneBroker
from .brokers.dhan import DhanBroker
from .brokers.base import Order


def run_backtest(args):
	bt = Backtester(YahooFinanceProvider())
	res = bt.run(symbol=args.symbol, start=args.start, end=args.end, capital=args.capital, risk_per_trade=args.risk_per_trade, interval=args.interval)
	print("Summary:")
	print(tabulate(res.summary.items(), headers=["Metric", "Value"]))
	if not res.trades.empty:
		print("\nTrades:")
		print(tabulate(res.trades.head(50).to_dict(orient="records"), headers="keys"))


def run_paper(args):
	provider = YahooFinanceProvider()
	strategy = SimpleOptionStrategy(SimpleOptionConfig())
	broker = AngelOneBroker() if args.broker == "angel" else DhanBroker()
	exec_engine = ExecutionEngine(broker, RiskConfig(capital=args.capital, risk_per_trade=args.risk_per_trade))
	print("Paper trading started. Press Ctrl+C to stop.")
	while True:
		end = datetime.utcnow()
		start = end - timedelta(days=5)
		bars = provider.get_history(args.symbol, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"), interval="1m")
		if not bars.empty:
			signal = strategy.generate_signals(bars)
			last_close = float(bars.iloc[-1]["Close"])  # proxy
			option_price = max(last_close * 0.03, 5.0)
			if signal.action == "buy_call":
				fill = exec_engine.maybe_enter("call", option_price)
				if fill:
					print(f"BUY CALL qty={fill.filled_qty} price={fill.avg_price}")
			elif signal.action == "buy_put":
				fill = exec_engine.maybe_enter("put", option_price)
				if fill:
					print(f"BUY PUT qty={fill.filled_qty} price={fill.avg_price}")
			exit_fill = exec_engine.maybe_exit(option_price)
			if exit_fill:
				print(f"EXIT qty={exit_fill.filled_qty} price={exit_fill.avg_price}")
		time.sleep(args.poll_seconds)


def main():
	parser = argparse.ArgumentParser(description="Algo trading tool for index & options")
	sub = parser.add_subparsers(dest="cmd")

	p1 = sub.add_parser("backtest")
	p1.add_argument("--symbol", required=True)
	p1.add_argument("--start", required=True)
	p1.add_argument("--end", required=True)
	p1.add_argument("--capital", type=float, default=200000)
	p1.add_argument("--risk-per-trade", type=float, default=0.01)
	p1.add_argument("--interval", type=str, default="5m")
	p1.set_defaults(func=run_backtest)

	p2 = sub.add_parser("paper")
	p2.add_argument("--symbol", required=True)
	p2.add_argument("--capital", type=float, default=200000)
	p2.add_argument("--risk-per-trade", type=float, default=0.01)
	p2.add_argument("--poll-seconds", type=int, default=60)
	p2.add_argument("--broker", choices=["angel", "dhan"], default="angel")
	p2.set_defaults(func=run_paper)

	args = parser.parse_args()
	if not hasattr(args, "func"):
		parser.print_help()
		return
	args.func(args)


if __name__ == "__main__":
	main()