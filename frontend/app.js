const byId = (id) => document.getElementById(id);

const el = {
  apiBase: byId("apiBase"),
  symbols: byId("symbols"),
  startDate: byId("startDate"),
  endDate: byId("endDate"),
  interval: byId("interval"),
  algorithm: byId("algorithm"),
  maxWeight: byId("maxWeight"),
  btnStatus: byId("btnStatus"),
  btnRun: byId("btnRun"),
  btnExport: byId("btnExport"),
  btnPdf: byId("btnPdf"),
  statusBox: byId("statusBox"),
  symbol: byId("mSymbol"),
  objective: byId("mObjective"),
  objValue: byId("mObjValue"),
  expectedReturn: byId("mReturn"),
  elapsed: byId("mElapsed"),
  portVol: byId("mPortVol"),
  sharpe: byId("mSharpe"),
  weights: byId("weights"),
  riskPct: byId("riskPct"),
  raw: byId("raw"),
  insightRiskAsset: byId("insightRiskAsset"),
  insightMinRiskAsset: byId("insightMinRiskAsset"),
  insightBestSharpe: byId("insightBestSharpe"),
  insightMinVol: byId("insightMinVol"),
};

if (window.OTIMIZADOR_API_BASE_URL) {
  el.apiBase.value = window.OTIMIZADOR_API_BASE_URL;
}

function setStatus(message, isError = false) {
  el.statusBox.textContent = message;
  el.statusBox.style.background = isError ? "#fde8e8" : "#e4f3ea";
  el.statusBox.style.borderColor = isError ? "#f5b5b5" : "#bfddcb";
  el.statusBox.style.color = isError ? "#7a1d1d" : "#214d31";
}

function parseSymbols() {
  return el.symbols.value
    .split(",")
    .map((item) => item.trim().toUpperCase())
    .filter(Boolean);
}

function parseMaxWeight() {
  const value = Number.parseFloat(el.maxWeight.value);
  if (!Number.isFinite(value)) return null;
  return value;
}

function formatNumber(value, digits = 8) {
  if (typeof value !== "number" || Number.isNaN(value)) return "-";
  return value.toFixed(digits);
}

function formatPct(value, digits = 2) {
  if (typeof value !== "number" || Number.isNaN(value)) return "-";
  return `${(value * 100).toFixed(digits)}%`;
}

function resetInsights() {
  el.insightRiskAsset.textContent = "-";
  el.insightMinRiskAsset.textContent = "-";
  el.insightBestSharpe.textContent = "-";
  el.insightMinVol.textContent = "-";
}

function findTopRiskAsset(riskMap) {
  const entries = Object.entries(riskMap || {});
  if (!entries.length) return null;
  return entries.reduce((best, current) => (current[1] > best[1] ? current : best));
}

function findMinRiskAsset(riskMap) {
  const entries = Object.entries(riskMap || {});
  if (!entries.length) return null;
  return entries.reduce((best, current) => (current[1] < best[1] ? current : best));
}

function applyInsightsSingle(data) {
  const meta = data.result?.metadata || {};
  const topRisk = findTopRiskAsset(meta.risk_contribution_pct || {});
  const minRisk = findMinRiskAsset(meta.risk_contribution_pct || {});

  if (topRisk) {
    el.insightRiskAsset.textContent = `${topRisk[0]} (${formatPct(topRisk[1])})`;
  } else {
    el.insightRiskAsset.textContent = "-";
  }

  if (minRisk) {
    el.insightMinRiskAsset.textContent = `${minRisk[0]} (${formatPct(minRisk[1])})`;
  } else {
    el.insightMinRiskAsset.textContent = "-";
  }

  el.insightBestSharpe.textContent = `${data.result?.algorithm || "-"} (${formatNumber(meta.sharpe_ratio, 6)})`;
  el.insightMinVol.textContent = `${data.result?.algorithm || "-"} (${formatNumber(meta.portfolio_volatility, 8)})`;
}

function applyInsightsAll(data) {
  const summary = data.comparison?.summary || [];
  const winner = data.comparison?.winner;

  const withSharpe = summary.filter((item) => typeof item.sharpe_ratio === "number");
  const withVol = summary.filter(
    (item) => typeof item.portfolio_volatility === "number",
  );

  const bestSharpe = withSharpe.length
    ? withSharpe.reduce((best, cur) => (cur.sharpe_ratio > best.sharpe_ratio ? cur : best))
    : null;

  const minVol = withVol.length
    ? withVol.reduce((best, cur) =>
        cur.portfolio_volatility < best.portfolio_volatility ? cur : best,
      )
    : null;

  const winnerItem = summary.find((item) => item.algorithm === winner) || null;
  const topRisk = winnerItem ? findTopRiskAsset(winnerItem.risk_contribution_pct || {}) : null;
  const minRisk = winnerItem ? findMinRiskAsset(winnerItem.risk_contribution_pct || {}) : null;

  if (topRisk && winnerItem) {
    el.insightRiskAsset.textContent = `${topRisk[0]} (${formatPct(topRisk[1])}) em ${winnerItem.algorithm}`;
  } else {
    el.insightRiskAsset.textContent = "-";
  }

  if (minRisk && winnerItem) {
    el.insightMinRiskAsset.textContent = `${minRisk[0]} (${formatPct(minRisk[1])}) em ${winnerItem.algorithm}`;
  } else {
    el.insightMinRiskAsset.textContent = "-";
  }

  if (bestSharpe) {
    el.insightBestSharpe.textContent = `${bestSharpe.algorithm} (${formatNumber(bestSharpe.sharpe_ratio, 6)})`;
  } else {
    el.insightBestSharpe.textContent = "-";
  }

  if (minVol) {
    el.insightMinVol.textContent = `${minVol.algorithm} (${formatNumber(minVol.portfolio_volatility, 8)})`;
  } else {
    el.insightMinVol.textContent = "-";
  }
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  let data = null;
  try {
    data = await response.json();
  } catch {
    data = { message: await response.text() };
  }

  if (!response.ok) {
    throw new Error(data?.message || `HTTP ${response.status}`);
  }
  return data;
}

function renderSingle(data) {
  const meta = data.result?.metadata || {};
  el.symbol.textContent = (data.symbols || []).join(", ") || data.symbol || "-";
  el.objective.textContent = data.objective ?? "-";
  el.objValue.textContent = formatNumber(data.result?.objective_value, 8);
  el.expectedReturn.textContent = formatNumber(data.result?.expected_return, 8);
  el.elapsed.textContent = formatNumber(data.result?.elapsed_ms, 2);
  el.portVol.textContent = formatNumber(meta.portfolio_volatility, 8);
  el.sharpe.textContent = formatNumber(meta.sharpe_ratio, 6);
  el.weights.textContent = JSON.stringify(data.result?.weights ?? {}, null, 2);
  el.riskPct.textContent = JSON.stringify(meta.risk_contribution_pct ?? {}, null, 2);
  applyInsightsSingle(data);
}

function renderAll(data) {
  const summary = data.comparison?.summary || [];
  const winner = data.comparison?.winner;
  const winnerItem = summary.find((item) => item.algorithm === winner) || null;

  el.symbol.textContent = (data.symbols || []).join(", ") || data.symbol || "-";
  el.objective.textContent = data.objective ?? "-";
  el.objValue.textContent = winnerItem ? formatNumber(winnerItem.objective_value, 8) : "-";
  el.expectedReturn.textContent = winnerItem
    ? formatNumber(winnerItem.expected_return, 8)
    : "-";
  el.elapsed.textContent = winnerItem ? formatNumber(winnerItem.elapsed_ms, 2) : "-";
  el.portVol.textContent = winnerItem
    ? formatNumber(winnerItem.portfolio_volatility, 8)
    : "-";
  el.sharpe.textContent = winnerItem ? formatNumber(winnerItem.sharpe_ratio, 6) : "-";
  el.weights.textContent = JSON.stringify(summary, null, 2);
  el.riskPct.textContent = JSON.stringify(
    summary.map((item) => ({
      algorithm: item.algorithm,
      risk_contribution_pct: item.risk_contribution_pct,
    })),
    null,
    2,
  );
  applyInsightsAll(data);
}

el.btnStatus.addEventListener("click", async () => {
  const baseUrl = el.apiBase.value.trim().replace(/\/$/, "");
  setStatus("Checando status da API...");
  try {
    let data;
    try {
      data = await fetchJson(`${baseUrl}/status`, { method: "GET" });
    } catch {
      // Fallback para APIs que expõem apenas /status/{execution_id}
      data = await fetchJson(`${baseUrl}/status/ping`, { method: "GET" });
    }
    setStatus(`API online: ${data.status}`);
    el.raw.textContent = JSON.stringify(data, null, 2);
  } catch (error) {
    setStatus(`Falha no status: ${error.message}`, true);
  }
});

el.btnRun.addEventListener("click", async () => {
  const baseUrl = el.apiBase.value.trim().replace(/\/$/, "");
  const symbols = parseSymbols();
  const startDate = el.startDate.value.trim();
  const endDate = el.endDate.value.trim();
  const interval = el.interval.value.trim();
  const algorithm = el.algorithm.value;
  const maxWeight = parseMaxWeight();

  if (symbols.length < 1) {
    setStatus("Informe pelo menos 1 ativo.", true);
    return;
  }
  if (maxWeight === null || maxWeight <= 0 || maxWeight > 1) {
    setStatus("Max Weight precisa estar entre 0 e 1.", true);
    return;
  }
  if (!startDate || !endDate) {
    setStatus("Informe data inicial e final.", true);
    return;
  }

  setStatus(`Executando ${algorithm} para ${symbols.join(", ")}...`);
  try {
    const data = await fetchJson(`${baseUrl}/optimize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        algorithm,
        symbols,
        start_date: startDate,
        end_date: endDate,
        interval,
        max_weight: maxWeight,
      }),
    });

    if (algorithm === "all") {
      renderAll(data);
    } else {
      renderSingle(data);
    }

    el.raw.textContent = JSON.stringify(data, null, 2);
    setStatus("Otimizacao concluida com sucesso.");
  } catch (error) {
    resetInsights();
    setStatus(`Falha na otimizacao: ${error.message}`, true);
  }
});

el.btnExport.addEventListener("click", async () => {
  const baseUrl = el.apiBase.value.trim().replace(/\/$/, "");
  const symbols = parseSymbols();
  const startDate = el.startDate.value.trim();
  const endDate = el.endDate.value.trim();
  const interval = el.interval.value.trim();
  const maxWeight = parseMaxWeight();

  if (symbols.length < 1) {
    setStatus("Informe pelo menos 1 ativo.", true);
    return;
  }
  if (!startDate || !endDate) {
    setStatus("Informe data inicial e final.", true);
    return;
  }
  if (maxWeight === null || maxWeight <= 0 || maxWeight > 1) {
    setStatus("Max Weight precisa estar entre 0 e 1.", true);
    return;
  }

  setStatus("Gerando exportacao de resultados...");
  try {
    const data = await fetchJson(`${baseUrl}/export`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        algorithm: "all",
        symbols,
        start_date: startDate,
        end_date: endDate,
        interval,
        max_weight: maxWeight,
      }),
    });
    el.raw.textContent = JSON.stringify(data, null, 2);
    setStatus("Exportacao concluida.");
  } catch (error) {
    setStatus(`Falha na exportacao: ${error.message}`, true);
  }
});

el.btnPdf.addEventListener("click", async () => {
  const baseUrl = el.apiBase.value.trim().replace(/\/$/, "");
  const symbols = parseSymbols();
  const startDate = el.startDate.value.trim();
  const endDate = el.endDate.value.trim();
  const interval = el.interval.value.trim();
  const maxWeight = parseMaxWeight();

  if (symbols.length < 1) {
    setStatus("Informe pelo menos 1 ativo.", true);
    return;
  }
  if (!startDate || !endDate) {
    setStatus("Informe data inicial e final.", true);
    return;
  }
  if (maxWeight === null || maxWeight <= 0 || maxWeight > 1) {
    setStatus("Max Weight precisa estar entre 0 e 1.", true);
    return;
  }

  setStatus("Gerando PDF do relatorio...");
  try {
    const response = await fetch(`${baseUrl}/report/pdf`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        algorithm: "all",
        symbols,
        start_date: startDate,
        end_date: endDate,
        interval,
        max_weight: maxWeight,
      }),
    });

    if (!response.ok) {
      let errorData = { message: `HTTP ${response.status}` };
      try {
        errorData = await response.json();
      } catch {
        errorData = { message: await response.text() };
      }
      throw new Error(errorData?.message || `HTTP ${response.status}`);
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `relatorio_otimizador_${startDate}_${endDate}.pdf`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);

    setStatus("PDF gerado e download iniciado.");
  } catch (error) {
    setStatus(`Falha ao gerar PDF: ${error.message}`, true);
  }
});
