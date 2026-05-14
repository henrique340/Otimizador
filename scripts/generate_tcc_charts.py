"""Gera pacote de graficos para TCC com base no experimento de otimizacao."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from otimizador.algorithms.genetic import run_genetic_algorithm
from otimizador.algorithms.linear_programming import run_linear_programming
from otimizador.algorithms.simulated_annealing import run_simulated_annealing
from otimizador.application import run_full_experiment
from otimizador.data.features import build_feature_set
from otimizador.data.ingestion import fetch_prices
from otimizador.domain.config import load_config_from_env
from otimizador.domain.models import OptimizationRequest
from otimizador.domain.objective import LinearRiskAdjustedObjective


def _parse_symbols(value: str | None) -> list[str] | None:
    if not value:
        return None
    parsed = [item.strip().upper() for item in value.split(",") if item.strip()]
    return parsed or None


def _portfolio_metrics(weights: np.ndarray, returns: np.ndarray) -> tuple[float, float, float]:
    expected_return = float(np.mean(returns @ weights))
    volatility = float(np.std(returns @ weights, ddof=0))
    sharpe = float(expected_return / volatility) if volatility > 0 else 0.0
    return expected_return, volatility, sharpe


def _build_request(
    symbols: list[str] | None,
    period: str | None,
    start_date: str | None,
    end_date: str | None,
    interval: str | None,
    max_weight: float | None,
) -> tuple[
    OptimizationRequest,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    list[str],
    dict[str, object],
]:
    cfg = load_config_from_env()

    data_cfg = cfg.data
    if symbols:
        data_cfg = replace(data_cfg, symbols=symbols)
    if period:
        data_cfg = replace(data_cfg, period=period)
    if start_date:
        data_cfg = replace(data_cfg, start_date=start_date)
    if end_date:
        data_cfg = replace(data_cfg, end_date=end_date)
    if interval:
        data_cfg = replace(data_cfg, interval=interval)

    optimizer_cfg = cfg.optimizer
    if max_weight is not None:
        optimizer_cfg = replace(optimizer_cfg, max_weight=max_weight)

    cfg = replace(cfg, data=data_cfg, optimizer=optimizer_cfg)

    prices = fetch_prices(cfg.data)
    feature_set = build_feature_set(cfg.data.symbols, prices)

    request = OptimizationRequest(
        symbol=feature_set.symbol,
        feature_names=feature_set.feature_names,
        expected_returns=feature_set.expected_returns,
        volatility=feature_set.volatility,
        covariance_matrix=feature_set.covariance_matrix,
        risk_aversion=cfg.optimizer.risk_aversion,
        max_weight=cfg.optimizer.max_weight,
        seed=cfg.optimizer.random_seed,
        metadata={
            "symbols": cfg.data.symbols,
            "period": cfg.data.period,
            "start_date": cfg.data.start_date,
            "end_date": cfg.data.end_date,
            "interval": cfg.data.interval,
            "samples": len(feature_set.frame),
            "max_weight": cfg.optimizer.max_weight,
        },
    )

    return (
        request,
        prices[feature_set.feature_names].to_numpy(dtype=float),
        np.array(prices.index),
        feature_set.frame.to_numpy(dtype=float),
        feature_set.feature_names,
        {
            "period": cfg.data.period,
            "start_date": cfg.data.start_date,
            "end_date": cfg.data.end_date,
            "interval": cfg.data.interval,
            "symbols": cfg.data.symbols,
            "ga_population_size": cfg.optimizer.ga_population_size,
            "ga_generations": cfg.optimizer.ga_generations,
            "sa_iterations": cfg.optimizer.sa_iterations,
            "sa_initial_temperature": cfg.optimizer.sa_initial_temperature,
            "sa_cooling_rate": cfg.optimizer.sa_cooling_rate,
        },
    )


def _save_01_price_normalized(
    output_dir: Path, prices: np.ndarray, dates: np.ndarray, assets: list[str]
) -> None:
    normalized = prices / prices[0]
    plt.figure(figsize=(12, 6))
    for idx, asset in enumerate(assets):
        plt.plot(dates, normalized[:, idx], label=asset)
    plt.title("01 - Evolucao de Precos Normalizados")
    plt.xlabel("Data")
    plt.ylabel("Preco Normalizado")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(output_dir / "01_precos_normalizados.png", dpi=150)
    plt.close()


def _save_02_returns_distribution(
    output_dir: Path, returns: np.ndarray, assets: list[str]
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for idx, asset in enumerate(assets):
        axes[0].hist(returns[:, idx], bins=30, alpha=0.4, label=asset)
    axes[0].set_title("Histograma de Retornos")
    axes[0].set_xlabel("Retorno Diario")
    axes[0].set_ylabel("Frequencia")
    axes[0].grid(alpha=0.2)
    axes[0].legend()

    axes[1].boxplot([returns[:, i] for i in range(len(assets))], tick_labels=assets)
    axes[1].set_title("Boxplot de Retornos")
    axes[1].set_ylabel("Retorno Diario")
    axes[1].grid(alpha=0.2)

    fig.suptitle("02 - Distribuicao de Retornos")
    fig.tight_layout()
    fig.savefig(output_dir / "02_distribuicao_retornos.png", dpi=150)
    plt.close(fig)


def _save_03_rolling_vol(
    output_dir: Path,
    returns: np.ndarray,
    dates: np.ndarray,
    assets: list[str],
    rolling_window: int,
) -> None:
    plt.figure(figsize=(12, 6))
    for idx, asset in enumerate(assets):
        series = returns[:, idx]
        kernel = np.ones(rolling_window, dtype=float) / rolling_window
        mean = np.convolve(series, kernel, mode="valid")
        mean_sq = np.convolve(series * series, kernel, mode="valid")
        var = np.maximum(mean_sq - mean * mean, 0.0)
        rolling_std = np.sqrt(var)
        plt.plot(dates[rolling_window - 1 :], rolling_std, label=asset)

    plt.title(f"03 - Volatilidade Movel ({rolling_window} janelas)")
    plt.xlabel("Data")
    plt.ylabel("Volatilidade")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(output_dir / "03_volatilidade_movel.png", dpi=150)
    plt.close()


def _save_04_corr_heatmap(output_dir: Path, returns: np.ndarray, assets: list[str]) -> None:
    corr = np.corrcoef(returns.T)
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(assets)))
    ax.set_yticks(range(len(assets)))
    ax.set_xticklabels(assets, rotation=45, ha="right")
    ax.set_yticklabels(assets)
    for i in range(len(assets)):
        for j in range(len(assets)):
            ax.text(j, i, f"{corr[i, j]:.2f}", ha="center", va="center", fontsize=9)
    ax.set_title("04 - Heatmap de Correlacao")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(output_dir / "04_heatmap_correlacao.png", dpi=150)
    plt.close(fig)


def _save_05_weights(
    output_dir: Path, assets: list[str], algo_weights: dict[str, np.ndarray]
) -> None:
    algo_names = list(algo_weights.keys())
    x = np.arange(len(assets), dtype=float)
    width = 0.22

    fig, ax = plt.subplots(figsize=(12, 6))
    for idx, name in enumerate(algo_names):
        ax.bar(x + (idx - 1) * width, algo_weights[name], width=width, label=name)

    ax.set_xticks(x)
    ax.set_xticklabels(assets)
    ax.set_title("05 - Pesos por Algoritmo")
    ax.set_ylabel("Peso")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "05_pesos_algoritmos.png", dpi=150)
    plt.close(fig)


def _save_06_metrics(
    output_dir: Path,
    algo_weights: dict[str, np.ndarray],
    returns: np.ndarray,
    objective_values: dict[str, float],
    elapsed_ms: dict[str, float],
) -> None:
    names = list(algo_weights.keys())
    expected = []
    vol = []
    sharpe = []
    obj = []
    elapsed = []

    for name in names:
        er, vv, ss = _portfolio_metrics(algo_weights[name], returns)
        expected.append(er)
        vol.append(vv)
        sharpe.append(ss)
        obj.append(objective_values[name])
        elapsed.append(elapsed_ms[name])

    fig, axes = plt.subplots(1, 5, figsize=(20, 4))
    data = [obj, expected, vol, sharpe, elapsed]
    titles = [
        "Objective",
        "Expected Return",
        "Volatility",
        "Sharpe",
        "Elapsed (ms)",
    ]

    for idx in range(5):
        axes[idx].bar(names, data[idx], color="#2c7fb8")
        axes[idx].set_title(titles[idx])
        axes[idx].tick_params(axis="x", rotation=20)
        axes[idx].grid(axis="y", alpha=0.25)

    fig.suptitle("06 - Metricas por Algoritmo")
    fig.tight_layout()
    fig.savefig(output_dir / "06_metricas_algoritmos.png", dpi=150)
    plt.close(fig)


def _save_07_frontier(
    output_dir: Path,
    request: OptimizationRequest,
    returns: np.ndarray,
    algo_weights: dict[str, np.ndarray],
    samples: int,
) -> None:
    rng = np.random.default_rng(request.seed)
    risks = []
    rets = []

    for _ in range(samples):
        w = rng.dirichlet(np.ones(len(request.feature_names)))
        w = np.clip(w, 0.0, request.max_weight)
        w = w / np.sum(w)
        er, vv, _ = _portfolio_metrics(w, returns)
        risks.append(vv)
        rets.append(er)

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.scatter(risks, rets, s=10, alpha=0.25, label="Portfolios Aleatorios")

    for name, weights in algo_weights.items():
        er, vv, _ = _portfolio_metrics(weights, returns)
        ax.scatter([vv], [er], s=120, marker="X", label=name)

    ax.set_title("07 - Fronteira Risco x Retorno")
    ax.set_xlabel("Risco (Volatilidade)")
    ax.set_ylabel("Retorno Esperado")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "07_fronteira_risco_retorno.png", dpi=150)
    plt.close(fig)


def _save_08_convergence(
    output_dir: Path,
    request: OptimizationRequest,
    objective: LinearRiskAdjustedObjective,
    ga_population_size: int,
    sa_initial_temperature: float,
    sa_cooling_rate: float,
) -> None:
    ga_steps = [5, 10, 20, 30, 40, 50, 75, 100]
    sa_steps = [20, 40, 60, 80, 120, 160, 220, 300]

    ga_scores = []
    for g in ga_steps:
        result = run_genetic_algorithm(request, objective, ga_population_size, g)
        ga_scores.append(result.objective_value)

    sa_scores = []
    for it in sa_steps:
        result = run_simulated_annealing(
            request, objective, it, sa_initial_temperature, sa_cooling_rate
        )
        sa_scores.append(result.objective_value)

    lp_score = run_linear_programming(request, objective).objective_value

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(ga_steps, ga_scores, marker="o", label="GA")
    ax.plot(sa_steps, sa_scores, marker="s", label="SA")
    ax.axhline(lp_score, color="black", linestyle="--", label="LP")
    ax.set_title("08 - Curva de Convergencia")
    ax.set_xlabel("Iteracoes/geracoes")
    ax.set_ylabel("Objective Value")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "08_convergencia_algoritmos.png", dpi=150)
    plt.close(fig)


def _save_09_backtest(
    output_dir: Path,
    returns: np.ndarray,
    dates: np.ndarray,
    algo_weights: dict[str, np.ndarray],
) -> dict[str, np.ndarray]:
    equity_curves: dict[str, np.ndarray] = {}

    fig, ax = plt.subplots(figsize=(12, 6))
    for name, weights in algo_weights.items():
        portfolio_ret = returns @ weights
        equity = np.cumprod(1.0 + portfolio_ret)
        equity_curves[name] = equity
        ax.plot(dates, equity, label=name)

    ax.set_title("09 - Backtest Acumulado (In-sample)")
    ax.set_xlabel("Data")
    ax.set_ylabel("Valor Acumulado")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "09_backtest_acumulado.png", dpi=150)
    plt.close(fig)

    return equity_curves


def _save_10_drawdown(output_dir: Path, dates: np.ndarray, equity_curves: dict[str, np.ndarray]) -> None:
    fig, ax = plt.subplots(figsize=(12, 6))
    for name, equity in equity_curves.items():
        running_max = np.maximum.accumulate(equity)
        drawdown = (equity / running_max) - 1.0
        ax.plot(dates, drawdown, label=name)

    ax.set_title("10 - Drawdown por Algoritmo")
    ax.set_xlabel("Data")
    ax.set_ylabel("Drawdown")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "10_drawdown_algoritmos.png", dpi=150)
    plt.close(fig)


def _write_summary(output_dir: Path, context: dict[str, object]) -> None:
    lines = [
        "# Graficos TCC - Otimizador",
        "",
        f"- Simbolos: {', '.join(context['symbols'])}",
        f"- Periodo: {context['period']}",
        f"- Start Date: {context['start_date']}",
        f"- End Date: {context['end_date']}",
        f"- Intervalo: {context['interval']}",
        "",
        "Arquivos gerados:",
        "- 01_precos_normalizados.png",
        "- 02_distribuicao_retornos.png",
        "- 03_volatilidade_movel.png",
        "- 04_heatmap_correlacao.png",
        "- 05_pesos_algoritmos.png",
        "- 06_metricas_algoritmos.png",
        "- 07_fronteira_risco_retorno.png",
        "- 08_convergencia_algoritmos.png",
        "- 09_backtest_acumulado.png",
        "- 10_drawdown_algoritmos.png",
    ]
    (output_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gerador de graficos de TCC")
    parser.add_argument(
        "--symbols", type=str, default=None, help="Ex: PETR4.SA,VALE3.SA,ITUB4.SA"
    )
    parser.add_argument("--period", type=str, default=None, help="Ex: 2y")
    parser.add_argument("--start-date", type=str, default=None, help="Ex: 2015-01-01")
    parser.add_argument("--end-date", type=str, default=None, help="Ex: 2025-12-31")
    parser.add_argument("--interval", type=str, default=None, help="Ex: 1d")
    parser.add_argument(
        "--max-weight", type=float, default=None, help="Peso maximo por ativo"
    )
    parser.add_argument(
        "--rolling-window",
        type=int,
        default=21,
        help="Janela da volatilidade movel",
    )
    parser.add_argument(
        "--frontier-samples", type=int, default=1500, help="Amostras da fronteira"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="docs/figures",
        help="Diretorio de saida dos graficos",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    symbols = _parse_symbols(args.symbols)

    request, prices, dates_prices, returns, assets, context = _build_request(
        symbols=symbols,
        period=args.period,
        start_date=args.start_date,
        end_date=args.end_date,
        interval=args.interval,
        max_weight=args.max_weight,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    experiment = run_full_experiment(
        symbols=assets,
        period=context["period"],
        start_date=context["start_date"],
        end_date=context["end_date"],
        interval=context["interval"],
        max_weight=request.max_weight,
    )

    algo_weights: dict[str, np.ndarray] = {}
    objective_values: dict[str, float] = {}
    elapsed_ms: dict[str, float] = {}

    for result in experiment["results"]:
        name = result["algorithm"]
        ordered_weights = [result["weights"][asset] for asset in assets]
        algo_weights[name] = np.array(ordered_weights, dtype=float)
        objective_values[name] = float(result["objective_value"])
        elapsed_ms[name] = float(result["elapsed_ms"])

    dates_returns = dates_prices[1:]

    _save_01_price_normalized(output_dir, prices, dates_prices, assets)
    _save_02_returns_distribution(output_dir, returns, assets)
    _save_03_rolling_vol(output_dir, returns, dates_returns, assets, args.rolling_window)
    _save_04_corr_heatmap(output_dir, returns, assets)
    _save_05_weights(output_dir, assets, algo_weights)
    _save_06_metrics(output_dir, algo_weights, returns, objective_values, elapsed_ms)
    _save_07_frontier(output_dir, request, returns, algo_weights, args.frontier_samples)
    _save_08_convergence(
        output_dir,
        request,
        LinearRiskAdjustedObjective(risk_aversion=request.risk_aversion),
        context["ga_population_size"],
        context["sa_initial_temperature"],
        context["sa_cooling_rate"],
    )
    curves = _save_09_backtest(output_dir, returns, dates_returns, algo_weights)
    _save_10_drawdown(output_dir, dates_returns, curves)

    _write_summary(output_dir, context)
    print(f"Graficos gerados com sucesso em: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
