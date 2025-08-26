from typer import Typer

app = Typer(help="QuantOps CLI")

from .commands import backtest_run, live_run  # noqa: E402

app.command(name="backtest")(backtest_run)
app.command(name="live")(live_run)