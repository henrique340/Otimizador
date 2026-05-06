from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from otimizador.application import run_full_experiment

ALGORITHM_OPTIONS = {
    "linear_programming",
    "genetic_algorithm",
    "simulated_annealing",
    "all",
}

app = FastAPI(title="Otimizador API", version="0.3.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OptimizeRequest(BaseModel):
    algorithm: Literal[
        "linear_programming", "genetic_algorithm", "simulated_annealing", "all"
    ] = "linear_programming"
    symbols: list[str] | None = None
    period: str | None = None
    interval: str | None = None
    max_weight: float | None = None


@app.get("/status")
def status():
    return {"status": "ok", "service": "otimizador"}


@app.post("/optimize")
def optimize(payload: OptimizeRequest):
    if payload.algorithm not in ALGORITHM_OPTIONS:
        return JSONResponse(
            status_code=400,
            content={
                "error": "invalid_algorithm",
                "message": f"Algoritmo invalido: {payload.algorithm}",
                "allowed": sorted(ALGORITHM_OPTIONS),
            },
        )

    try:
        result = run_full_experiment(
            symbols=payload.symbols,
            period=payload.period,
            interval=payload.interval,
            max_weight=payload.max_weight,
        )
    except Exception as exc:
        return JSONResponse(
            status_code=502,
            content={
                "error": "data_ingestion_failed",
                "message": str(exc),
                "tip": "Verifique internet para Yahoo Finance ou adicione cache CSV local em /cache.",
            },
        )

    if payload.algorithm == "all":
        return result

    selected = next(
        (item for item in result["results"] if item["algorithm"] == payload.algorithm),
        None,
    )
    if selected is None:
        return JSONResponse(
            status_code=500,
            content={
                "error": "algorithm_not_found",
                "message": f"Resultado nao encontrado para {payload.algorithm}",
            },
        )

    return {
        "symbol": result["symbol"],
        "symbols": result["symbols"],
        "objective": result["objective"],
        "result": selected,
        "comparison": result["comparison"],
    }
