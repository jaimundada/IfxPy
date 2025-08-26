# OPTZ - Options Trading Toolkit

OPTZ is a Python toolkit for index and stock options algorithmic trading:
- Delayed data via yfinance provider (pluggable for paid real-time feeds)
- Option pricing (Black-Scholes) and strike selection
- Example strategy (momentum ATM with SL/TP)
- Minute-level backtesting with metrics
- Live runner with Paper broker; AngelOne and Dhan connectors (stubs)

## Install

```bash
pip install -r requirements.txt
```

## Quick start

Backtest NIFTY-like on a sample symbol (use US symbol if NSE minute data is unavailable):

```bash
python -m optz.cli backtest --symbol SPY --date 2024-08-02 --capital 100000 --strategy momentum_atm --iv 0.20
```

Run live paper trading (polls every minute):

```bash
python -m optz.cli live --symbol SPY --strategy momentum_atm --iv 0.20
```

Generate example config:

```bash
python -m optz.cli gen-config --path example_config.yaml
```

## Brokers
- Paper: built-in
- AngelOne (SmartAPI) and Dhan: stubs provided. Add your API keys and session handling. Use at your own risk.

## Data providers
The default provider uses yfinance (delayed). You can later plug in paid real-time sources by implementing `DataProvider`.

## Disclaimer
This software is for educational and research purposes only and is provided "AS IS" without warranty. Trading involves substantial risk. You are solely responsible for any decisions and outcomes. Use only with capital you can afford to lose.

