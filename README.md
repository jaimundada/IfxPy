# Index & Options Algo Trading Tool (Angel/Dhan connectors, Backtests)

This project provides a modular algorithmic trading framework focused on index and stock options trading for Indian markets. It includes:

- Delayed data provider via Yahoo Finance (`yfinance`) for indexes and equities
- Option pricing utilities (Black–Scholes, ATM strike selection)
- Strategy engine with targets, stop-loss, and risk sizing
- Broker connectors scaffolds for Angel One and Dhan (replace with live credentials)
- Execution engine for live/paper trading
- Minute-by-minute backtester with realistic fills and reporting
- CLI to run live (paper) and backtests

Note: Real-time feeds typically require paid vendor APIs. This repo ships with delayed data (Yahoo Finance). Steps to integrate paid data are outlined below.

## Quickstart

1) Python 3.10+

2) Install dependencies:

```bash
pip install -r requirements.txt
```

3) Backtest an index:

```bash
python -m algo_trader.cli backtest \
  --symbol "^NSEI" \
  --start "2024-09-01" \
  --end   "2024-09-10" \
  --strategy simple_option \
  --capital 200000 \
  --risk-per-trade 0.01
```

4) Paper trade (polling every 60s):

```bash
python -m algo_trader.cli paper \
  --symbol "^NSEI" \
  --strategy simple_option \
  --capital 200000 \
  --risk-per-trade 0.01 \
  --poll-seconds 60
```

- For Indian indices on Yahoo Finance, examples: `^NSEI` (NIFTY 50), `^NSEBANK` (BANKNIFTY). Availability of minute data can vary.

## Paid Real-time Data Integration

Replace `algo_trader/data_providers/yfinance_provider.py` with a provider that uses a paid data vendor:

- **TrueData**, **GlobalDataFeeds**, **Zerodha Kite Ticker**, **Angel One SmartAPI WebSocket**, **Dhan Market Data**
- Implement a class `MarketDataProvider` with methods: `stream_quotes`, `get_history`, `get_ltp`, `get_option_chain` (if available)
- Wire it in `algo_trader/cli.py` by selecting your provider via `--provider` flag or config YAML.

## Brokers (Angel One, Dhan)

This repo includes authenticated connector scaffolds you must complete with your API keys and tokens.

- Angel One: fill env vars `ANGEL_API_KEY`, `ANGEL_CLIENT_CODE`, `ANGEL_TOTP_SECRET`, etc.
- Dhan: fill env var `DHAN_ACCESS_TOKEN`.

Use `--mode live` in the future once you validate paper trading and have real-time data and exchange approvals. Trading involves risk.

## Strategies

- `simple_option`: Index options, selects ATM strike based on underlying, places entries on breakout with configurable target and SL, uses position sizing by risk.

You can add your own strategies by implementing `BaseStrategy`.

## Backtesting

- Minute-by-minute engine, fills at next minute open by default, configurable slippage and fees
- PnL report summary and equity curve

Example report output includes trades table and summary stats (win rate, profit factor, max drawdown).

## Disclaimers

This software is for educational purposes only. Markets carry risk. You are responsible for complying with applicable laws, exchange/broker rules, approvals and for validating behavior on paper before live deployment.

