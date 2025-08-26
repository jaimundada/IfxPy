from __future__ import annotations

import datetime
from typing import Optional
import yaml
from pydantic import BaseModel, Field


class BacktestConfig(BaseModel):
    date: datetime.date = Field(..., description="Trading session date")
    capital: float = Field(100000.0, description="Starting capital")


class MomentumATMStrategyConfig(BaseModel):
    iv: float = Field(0.20, description="Assumed IV (annualized)")
    sl_pct: float = Field(0.30, description="Stop loss percent of premium")
    tp_pct: float = Field(0.50, description="Take profit percent of premium")
    ma_fast: int = Field(9, description="Fast moving average length")
    ma_slow: int = Field(21, description="Slow moving average length")
    strike_step: float = Field(1.0, description="Strike rounding step")
    option_multiplier: int = Field(100, description="Contract multiplier (US equity = 100)")


class StrategyConfig(BaseModel):
    momentum_atm: MomentumATMStrategyConfig = Field(default_factory=MomentumATMStrategyConfig)


class BrokerConfig(BaseModel):
    paper: dict = Field(default_factory=dict)
    angel: dict = Field(default_factory=dict)
    dhan: dict = Field(default_factory=dict)


class AppConfig(BaseModel):
    symbol: str
    backtest: BacktestConfig
    strategy: StrategyConfig = Field(default_factory=StrategyConfig)
    broker: BrokerConfig = Field(default_factory=BrokerConfig)

    @staticmethod
    def from_yaml(path: str) -> "AppConfig":
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return AppConfig(**data)


def write_example_config(path: str) -> None:
    example = {
        "symbol": "SPY",
        "backtest": {"date": "2024-08-02", "capital": 100000},
        "strategy": {
            "momentum_atm": {
                "iv": 0.20,
                "sl_pct": 0.30,
                "tp_pct": 0.50,
                "ma_fast": 9,
                "ma_slow": 21,
                "strike_step": 1.0,
                "option_multiplier": 100,
            }
        },
        "broker": {"paper": {}, "angel": {"api_key": ""}, "dhan": {"api_key": ""}},
    }
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(example, f, sort_keys=False)