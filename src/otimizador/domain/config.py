"""Configuracao do projeto via variaveis de ambiente."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _parse_symbols(value: str) -> list[str]:
    return [item.strip().upper() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class DataConfig:
    symbols: list[str] = field(default_factory=lambda: ["PETR4.SA"])
    period: str = "2y"
    start_date: str | None = None
    end_date: str | None = None
    interval: str = "1d"
    cache_dir: str = "cache"


@dataclass(frozen=True)
class OptimizerConfig:
    risk_aversion: float = 0.35
    max_weight: float = 0.6
    random_seed: int = 42
    ga_population_size: int = 32
    ga_generations: int = 50
    sa_iterations: int = 250
    sa_initial_temperature: float = 1.0
    sa_cooling_rate: float = 0.98


@dataclass(frozen=True)
class AppConfig:
    data: DataConfig
    optimizer: OptimizerConfig


def load_config_from_env() -> AppConfig:
    symbols_raw = os.getenv("OTIMIZADOR_SYMBOLS")
    if symbols_raw:
        symbols = _parse_symbols(symbols_raw)
    else:
        symbols = [os.getenv("OTIMIZADOR_SYMBOL", "PETR4.SA").strip().upper()]

    if not symbols:
        symbols = ["PETR4.SA"]

    return AppConfig(
        data=DataConfig(
            symbols=symbols,
            period=os.getenv("OTIMIZADOR_PERIOD", "2y"),
            start_date=os.getenv("OTIMIZADOR_START_DATE"),
            end_date=os.getenv("OTIMIZADOR_END_DATE"),
            interval=os.getenv("OTIMIZADOR_INTERVAL", "1d"),
            cache_dir=os.getenv("OTIMIZADOR_CACHE_DIR", "cache"),
        ),
        optimizer=OptimizerConfig(
            risk_aversion=float(os.getenv("OTIMIZADOR_RISK_AVERSION", "0.35")),
            max_weight=float(os.getenv("OTIMIZADOR_MAX_WEIGHT", "0.6")),
            random_seed=int(os.getenv("OTIMIZADOR_RANDOM_SEED", "42")),
            ga_population_size=int(os.getenv("OTIMIZADOR_GA_POPULATION", "32")),
            ga_generations=int(os.getenv("OTIMIZADOR_GA_GENERATIONS", "50")),
            sa_iterations=int(os.getenv("OTIMIZADOR_SA_ITERATIONS", "250")),
            sa_initial_temperature=float(
                os.getenv("OTIMIZADOR_SA_INITIAL_TEMPERATURE", "1.0")
            ),
            sa_cooling_rate=float(os.getenv("OTIMIZADOR_SA_COOLING_RATE", "0.98")),
        ),
    )
