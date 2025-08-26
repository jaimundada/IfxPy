import sys
import json
import typer
from typing import Optional
from datetime import datetime

from .config import AppConfig, write_example_config
from .backtest.engine import BacktestEngine
from .strategy.momentum_atm import MomentumATMStrategy, MomentumATMConfig
from .data.yfinance_provider import YFinanceProvider
from .data.synthetic_provider import SyntheticProvider
from .broker.paper import PaperBroker
from .live.runner import LiveRunner

app = typer.Typer(add_completion=False, help="OPTZ - Options Trading Toolkit")


@app.command()
def gen_config(path: str = typer.Option("example_config.yaml", "--path", help="Write example config here")):
	"""Generate an example YAML configuration file."""
	write_example_config(path)
	typer.echo(f"Wrote example config to {path}")


@app.command()
def backtest(
	config: Optional[str] = typer.Option(None, "--config", help="Path to YAML config"),
	symbol: str = typer.Option(None, "--symbol", help="Underlying symbol (e.g., ^NSEI, SPY)"),
	test_date: Optional[str] = typer.Option(None, "--date", help="YYYY-MM-DD trading session to backtest"),
	capital: float = typer.Option(100000.0, "--capital", help="Starting capital"),
	iv: float = typer.Option(0.20, "--iv", help="Implied vol (annualized) assumption for options pricing"),
	strategy: str = typer.Option("momentum_atm", "--strategy", help="Strategy name"),
	provider: str = typer.Option("yfinance", "--provider", help="Data provider: yfinance|synthetic"),
):
	"""Run a minute-level backtest over a single session."""
	if config:
		cfg = AppConfig.from_yaml(config)
		if symbol is None:
			symbol = cfg.symbol
		if test_date is None:
			test_date = cfg.backtest.date.isoformat()
		capital = cfg.backtest.capital or capital
		iv = cfg.strategy.momentum_atm.iv or iv

	provider = YFinanceProvider() if provider == "yfinance" else SyntheticProvider()
	broker = PaperBroker(starting_cash=capital)

	if strategy == "momentum_atm":
		strategy_cfg = MomentumATMConfig(assumed_iv=iv)
		strat = MomentumATMStrategy(strategy_cfg)
	else:
		raise typer.BadParameter(f"Unknown strategy: {strategy}")

	engine = BacktestEngine(provider=provider, broker=broker, strategy=strat)
	parsed_date = datetime.fromisoformat(test_date).date() if isinstance(test_date, str) else test_date
	results = engine.run_session(symbol=symbol, session_date=parsed_date)

	typer.echo(json.dumps(results, indent=2, default=str))


@app.command()
def live(
	symbol: str = typer.Option(..., "--symbol", help="Underlying symbol"),
	iv: float = typer.Option(0.20, "--iv", help="Implied vol (annualized) assumption for options pricing"),
	capital: float = typer.Option(100000.0, "--capital", help="Starting cash for Paper broker"),
	provider: str = typer.Option("yfinance", "--provider", help="Data provider: yfinance|synthetic"),
):
	"""Run live paper trading, polling data every minute."""
	data_provider = YFinanceProvider() if provider == "yfinance" else SyntheticProvider()
	broker = PaperBroker(starting_cash=capital)
	strategy_cfg = MomentumATMConfig(assumed_iv=iv)
	strat = MomentumATMStrategy(strategy_cfg)
	LiveRunner(provider=data_provider, broker=broker, strategy=strat).run(symbol)


if __name__ == "__main__":
	app()