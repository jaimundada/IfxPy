from datetime import datetime
import typer
from rich import print

from ..engine.backtester import Backtester
from ..strategies.index_options import IndexOptionsStrategy
from ..data_providers.yahoo import YahooProvider
from ..engine.execution import PaperExecutor
from ..engine.live_engine import LiveEngine


def backtest_run(
	start: str = typer.Option(..., help="Start date YYYY-MM-DD"),
	end: str = typer.Option(..., help="End date YYYY-MM-DD"),
	symbol: str = typer.Option("^NSEI", help="Index symbol, e.g., ^NSEI (Nifty 50)"),
	capital: float = typer.Option(100000.0, help="Initial capital"),
):
	start_dt = datetime.fromisoformat(start)
	end_dt = datetime.fromisoformat(end)
	provider = YahooProvider()
	strategy = IndexOptionsStrategy(index_symbol=symbol)
	executor = PaperExecutor(initial_cash=capital)
	bt = Backtester(provider, strategy, executor)
	result = bt.run(start_dt, end_dt)
	print(result.summary())


def live_run(
	symbol: str = typer.Option("^NSEI"),
	paper: bool = typer.Option(True, help="Paper trading if True"),
):
	provider = YahooProvider()
	strategy = IndexOptionsStrategy(index_symbol=symbol)
	executor = PaperExecutor() if paper else PaperExecutor()
	engine = LiveEngine(provider, strategy, executor)
	engine.run()
	print("Live loop exited")