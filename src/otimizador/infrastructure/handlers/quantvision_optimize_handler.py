"""Handler de otimizacao para Lambda."""

from __future__ import annotations

import json
import os
from pathlib import Path

from otimizador.application import run_full_experiment
from otimizador.domain.config import load_config_from_env
from otimizador.infrastructure.http import response


def _normalize_symbols(raw_symbols: object) -> list[str]:
    if not isinstance(raw_symbols, list):
        return []
    return [str(item).strip().upper() for item in raw_symbols if str(item).strip()]


def _build_cache_filename(
    *,
    symbols: list[str],
    period: str,
    start_date: str | None,
    end_date: str | None,
    interval: str,
) -> str:
    symbols_key = "__".join(symbols).replace(".", "_")
    if start_date or end_date:
        start_key = (start_date or "none").replace("-", "")
        end_key = (end_date or "none").replace("-", "")
        window_key = f"{start_key}_{end_key}"
    else:
        window_key = period
    return f"{symbols_key}_{window_key}_{interval}.csv"


def _download_cache_from_s3(payload: dict) -> None:
    bucket = os.getenv("OTIMIZADOR_S3_CACHE_BUCKET", "").strip()
    if not bucket:
        return

    try:
        import boto3
    except Exception:
        print("S3 cache: boto3 nao disponivel no ambiente.")
        return

    cfg = load_config_from_env().data
    symbols = _normalize_symbols(payload.get("symbols")) or cfg.symbols
    period = str(payload.get("period") or cfg.period)
    start_date = payload.get("start_date") or cfg.start_date
    end_date = payload.get("end_date") or cfg.end_date
    interval = str(payload.get("interval") or cfg.interval)

    cache_dir = Path(os.getenv("OTIMIZADOR_CACHE_DIR", cfg.cache_dir))
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ["OTIMIZADOR_CACHE_DIR"] = str(cache_dir)

    filename = _build_cache_filename(
        symbols=symbols,
        period=period,
        start_date=start_date,
        end_date=end_date,
        interval=interval,
    )
    local_path = cache_dir / filename
    if local_path.exists():
        return

    prefix = os.getenv("OTIMIZADOR_S3_CACHE_PREFIX", "cache").strip().strip("/")
    key = f"{prefix}/{filename}" if prefix else filename

    try:
        boto3.client("s3").download_file(bucket, key, str(local_path))
        print(f"S3 cache: baixado s3://{bucket}/{key} -> {local_path}")
    except Exception as exc:
        print(f"S3 cache: nao foi possivel baixar s3://{bucket}/{key}. Motivo: {exc}")


def lambda_handler(event, context):  # noqa: ARG001
    payload = {}
    body = event.get("body") if isinstance(event, dict) else None
    if isinstance(body, str) and body.strip():
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {}
    elif isinstance(body, dict):
        payload = body

    try:
        _download_cache_from_s3(payload)
        result = run_full_experiment(
            symbols=payload.get("symbols"),
            period=payload.get("period"),
            start_date=payload.get("start_date"),
            end_date=payload.get("end_date"),
            interval=payload.get("interval"),
            max_weight=payload.get("max_weight"),
        )
        return response(200, result)
    except Exception as exc:
        return response(
            502,
            {
                "error": "optimize_failed",
                "message": str(exc),
                "tip": (
                    "Verifique CloudWatch Logs e configure OTIMIZADOR_CACHE_DIR=/tmp/cache. "
                    "Se usar cache no S3, configure OTIMIZADOR_S3_CACHE_BUCKET e "
                    "OTIMIZADOR_S3_CACHE_PREFIX."
                ),
            },
        )
