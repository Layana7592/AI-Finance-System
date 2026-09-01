import { useEffect, useMemo, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000/api";

const INR = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 2,
});

const INR_COMPACT = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  notation: "compact",
  maximumFractionDigits: 1,
});

function firstDefined(...values) {
  return values.find(
    (value) => value !== undefined && value !== null
  );
}

function numberOrZero(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
}

function formatMoney(value) {
  return INR.format(numberOrZero(value));
}

function formatCompactMoney(value) {
  return INR_COMPACT.format(numberOrZero(value));
}

function formatPercent(value) {
  return `${numberOrZero(value).toFixed(2)}%`;
}

/*
 * IMPORTANT:
 * The dashboard API returns anomaly_percentage as 1.0,
 * meaning 1%.
 *
 * Do NOT multiply this value by 100.
 */
function normalizePercentage(value) {
  return numberOrZero(value);
}

/*
 * Model metrics from the API are decimal fractions:
 *
 * 1.0    -> 100%
 * 0.788  -> 78.8%
 * 0.884  -> 88.4%
 * 0.8966 -> 89.66%
 *
 * Therefore model metrics DO need conversion.
 */
function normalizeMetric(value) {
  const number = numberOrZero(value);

  if (number > 0 && number <= 1) {
    return number * 100;
  }

  return number;
}

function normalizeDateLabel(value) {
  if (!value) return "";

  const text = String(value);

  if (/^\d{4}-\d{2}$/.test(text)) {
    const [year, month] = text.split("-");

    const date = new Date(
      Number(year),
      Number(month) - 1,
      1
    );

    return date.toLocaleDateString("en-US", {
      month: "short",
      year: "2-digit",
    });
  }

  if (/^\d{4}-\d{2}-\d{2}/.test(text)) {
    const date = new Date(text);

    if (!Number.isNaN(date.getTime())) {
      return date.toLocaleDateString("en-US", {
        month: "short",
        year: "numeric",
      });
    }
  }

  return text;
}

function normalizeHistoricalData(data) {
  if (!Array.isArray(data)) return [];

  return data.map((item, index) => ({
    month: normalizeDateLabel(
      firstDefined(
        item?.month,
        item?.date,
        item?.period,
        item?.transaction_month,
        item?.label,
        index + 1
      )
    ),

    income: numberOrZero(
      firstDefined(
        item?.income,
        item?.total_income,
        item?.income_total,
        item?.credit,
        item?.credits
      )
    ),

    expense: numberOrZero(
      firstDefined(
        item?.expense,
        item?.total_expense,
        item?.expense_total,
        item?.debit,
        item?.debits
      )
    ),
  }));
}

function normalizeForecastData(data) {
  if (!Array.isArray(data)) return [];

  return data.map((item, index) => ({
    month: normalizeDateLabel(
      firstDefined(
        item?.month,
        item?.date,
        item?.period,
        item?.forecast_month,
        item?.label,
        `2026-${String(index + 1).padStart(2, "0")}`
      )
    ),

    income: numberOrZero(
      firstDefined(
        item?.income,
        item?.predicted_income,
        item?.forecast_income,
        item?.income_forecast
      )
    ),

    expense: numberOrZero(
      firstDefined(
        item?.expense,
        item?.predicted_expense,
        item?.forecast_expense,
        item?.expense_forecast
      )
    ),
  }));
}

function extractHistoricalData(payload) {
  const root = payload?.data ?? payload ?? {};

  const candidates = [
    root?.monthly_trends,
    root?.monthly_data,
    root?.monthly,
    root?.historical,
    root?.historical_data,
    root?.trends,

    payload?.monthly_trends,
    payload?.monthly_data,
    payload?.monthly,
    payload?.historical,
    payload?.historical_data,
    payload?.trends,

    root?.data?.monthly_trends,
    root?.data?.monthly_data,
    root?.data?.historical,
    root?.data?.monthly,
  ];

  for (const candidate of candidates) {
    const normalized = normalizeHistoricalData(candidate);

    if (normalized.length > 0) {
      return normalized;
    }
  }

  return [];
}

/*
 * IMPORTANT FIX:
 *
 * The actual dashboard API returns:
 *
 * "forecasts": [
 *   {
 *     "month": "2026-01",
 *     "predicted_income": ...,
 *     "predicted_expense": ...
 *   }
 * ]
 *
 * So forecasts MUST be checked first.
 */
function extractForecastData(payload) {
  const root = payload?.data ?? payload ?? {};

  const candidates = [
    root?.forecasts,

    root?.forecast,
    root?.forecast_data,
    root?.monthly_forecast,
    root?.forecast_monthly,

    root?.data?.forecasts,
    root?.data?.forecast,
    root?.data?.forecast_data,

    payload?.forecasts,
    payload?.forecast,
    payload?.forecast_data,
    payload?.monthly_forecast,
    payload?.forecast_monthly,
  ];

  for (const candidate of candidates) {
    const normalized = normalizeForecastData(candidate);

    if (normalized.length > 0) {
      return normalized;
    }
  }

  return [];
}

function extractDashboard(payload) {
  const root = payload?.data ?? payload ?? {};

  const fraud =
    root?.fraud_evaluation ??
    root?.fraud_detection ??
    root?.fraud ??
    {};

  const forecast =
    root?.forecast_evaluation ??
    root?.forecasting ??
    root?.forecast ??
    {};

  const dataset =
    root?.dataset ??
    root?.summary ??
    root?.overview ??
    {};

  const systemInfo =
    root?.system_info ??
    root?.systemInfo ??
    {};

  const incomeForecast =
    forecast?.income ??
    root?.income_forecast ??
    root?.incomeForecast ??
    {};

  const expenseForecast =
    forecast?.expense ??
    root?.expense_forecast ??
    root?.expenseForecast ??
    {};

  const statistical =
    fraud?.statistical_baseline ??
    fraud?.statistical ??
    root?.statistical_baseline ??
    root?.statistical ??
    {};

  const isolation =
    fraud?.isolation_forest ??
    fraud?.isolation ??
    root?.isolation_forest ??
    root?.isolation ??
    {};

  return {
    /*
     * -----------------------------
     * SUMMARY
     * -----------------------------
     */

    totalTransactions: numberOrZero(
      firstDefined(
        root?.total_transactions,
        dataset?.total_transactions,
        dataset?.transactions,
        root?.transactions
      )
    ),

    actualAnomalies: numberOrZero(
      firstDefined(
        root?.actual_anomalies,
        dataset?.actual_anomalies,
        fraud?.actual_anomalies,
        root?.anomalies
      )
    ),

    /*
     * IMPORTANT:
     * API gives anomaly_percentage = 1.0
     * and that means 1%.
     */
    anomalyPercentage: normalizePercentage(
      firstDefined(
        root?.anomaly_percentage,
        dataset?.anomaly_percentage,
        fraud?.anomaly_percentage
      )
    ),

    totalIncome: numberOrZero(
      firstDefined(
        root?.total_income,
        dataset?.total_income,
        root?.income
      )
    ),

    totalExpense: numberOrZero(
      firstDefined(
        root?.total_expense,
        dataset?.total_expense,
        root?.expense
      )
    ),

    /*
     * -----------------------------
     * SYSTEM INFORMATION
     * -----------------------------
     *
     * Actual API structure:
     *
     * "system_info": {
     *   "historical_months": 24,
     *   "training_months": 12,
     *   "validation_months": 12,
     *   "forecast_horizon": 12
     * }
     */

    historicalMonths: numberOrZero(
      firstDefined(
        systemInfo?.historical_months,
        systemInfo?.historicalMonths,

        root?.historical_months,
        forecast?.months,
        forecast?.historical_months,
        dataset?.months
      )
    ),

    trainingMonths: numberOrZero(
      firstDefined(
        systemInfo?.training_months,
        systemInfo?.trainingMonths,

        root?.training_months,
        forecast?.training_months
      )
    ),

    validationMonths: numberOrZero(
      firstDefined(
        systemInfo?.validation_months,
        systemInfo?.validationMonths,

        root?.validation_months,
        forecast?.validation_months
      )
    ),

    forecastHorizon: numberOrZero(
      firstDefined(
        systemInfo?.forecast_horizon,
        systemInfo?.forecastHorizon,

        root?.forecast_horizon,
        forecast?.forecast_horizon
      )
    ),

    /*
     * -----------------------------
     * STATISTICAL BASELINE
     * -----------------------------
     */

    statistical: {
      precision: normalizeMetric(
        firstDefined(
          statistical?.precision,
          statistical?.precision_score
        )
      ),

      recall: normalizeMetric(
        firstDefined(
          statistical?.recall,
          statistical?.recall_score
        )
      ),

      f1: normalizeMetric(
        firstDefined(
          statistical?.f1_score,
          statistical?.f1,
          statistical?.f1Score
        )
      ),

      confusionMatrix:
        statistical?.confusion_matrix ??
        statistical?.confusionMatrix ??
        [[0, 0], [0, 0]],
    },

    /*
     * -----------------------------
     * ISOLATION FOREST
     * -----------------------------
     */

    isolation: {
      precision: normalizeMetric(
        firstDefined(
          isolation?.precision,
          isolation?.precision_score
        )
      ),

      recall: normalizeMetric(
        firstDefined(
          isolation?.recall,
          isolation?.recall_score
        )
      ),

      f1: normalizeMetric(
        firstDefined(
          isolation?.f1_score,
          isolation?.f1,
          isolation?.f1Score
        )
      ),

      confusionMatrix:
        isolation?.confusion_matrix ??
        isolation?.confusionMatrix ??
        [[0, 0], [0, 0]],
    },

    /*
     * -----------------------------
     * INCOME FORECAST EVALUATION
     * -----------------------------
     */

    incomeForecast: {
      bestModel: firstDefined(
        incomeForecast?.best_model,
        incomeForecast?.bestModel,
        "Seasonal-Naive"
      ),

      mae: numberOrZero(
        incomeForecast?.seasonal_naive?.mae
      ),

      rmse: numberOrZero(
        incomeForecast?.seasonal_naive?.rmse
      ),

      mape: numberOrZero(
        incomeForecast?.seasonal_naive?.mape
      ),

      sarima: {
        mae: numberOrZero(
          incomeForecast?.sarima?.mae
        ),

        rmse: numberOrZero(
          incomeForecast?.sarima?.rmse
        ),

        mape: numberOrZero(
          incomeForecast?.sarima?.mape
        ),
      },
    },

    /*
     * -----------------------------
     * EXPENSE FORECAST EVALUATION
     * -----------------------------
     */

    expenseForecast: {
      bestModel: firstDefined(
        expenseForecast?.best_model,
        expenseForecast?.bestModel,
        "Seasonal-Naive"
      ),

      mae: numberOrZero(
        expenseForecast?.seasonal_naive?.mae
      ),

      rmse: numberOrZero(
        expenseForecast?.seasonal_naive?.rmse
      ),

      mape: numberOrZero(
        expenseForecast?.seasonal_naive?.mape
      ),

      sarima: {
        mae: numberOrZero(
          expenseForecast?.sarima?.mae
        ),

        rmse: numberOrZero(
          expenseForecast?.sarima?.rmse
        ),

        mape: numberOrZero(
          expenseForecast?.sarima?.mape
        ),
      },
    },
  };
}

async function fetchJSON(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      Accept: "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const error = new Error(
      `Request failed with status ${response.status}`
    );

    error.status = response.status;

    throw error;
  }

  return response.json();
}

function SectionHeader({
  eyebrow,
  title,
  description,
}) {
  return (
    <div className="section-header">
      <div>
        {eyebrow && (
          <div className="section-eyebrow">
            {eyebrow}
          </div>
        )}

        <h2>{title}</h2>

        {description && <p>{description}</p>}
      </div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  helper,
  icon,
  accent = "blue",
}) {
  return (
    <div className={`metric-card metric-${accent}`}>
      <div className="metric-top">
        <span className="metric-label">
          {label}
        </span>

        <span className="metric-icon">
          {icon}
        </span>
      </div>

      <div className="metric-value">
        {value}
      </div>

      <div className="metric-helper">
        {helper}
      </div>
    </div>
  );
}

function ModelMetricCard({
  title,
  precision,
  recall,
  f1,
  accent,
}) {
  return (
    <div className={`model-card ${accent}`}>
      <div className="model-card-heading">
        <div>
          <span className="model-kicker">
            Detection model
          </span>

          <h3>{title}</h3>
        </div>
      </div>

      <div className="model-metrics">
        <div>
          <span>Precision</span>

          <strong>
            {formatPercent(precision)}
          </strong>
        </div>

        <div>
          <span>Recall</span>

          <strong>
            {formatPercent(recall)}
          </strong>
        </div>

        <div>
          <span>F1 Score</span>

          <strong>
            {formatPercent(f1)}
          </strong>
        </div>
      </div>
    </div>
  );
}

function ConfusionMatrix({
  title,
  matrix,
}) {
  const safeMatrix =
    Array.isArray(matrix) &&
    matrix.length >= 2 &&
    Array.isArray(matrix[0]) &&
    matrix[0].length >= 2 &&
    Array.isArray(matrix[1]) &&
    matrix[1].length >= 2
      ? matrix
      : [
          [0, 0],
          [0, 0],
        ];

  const tn = numberOrZero(
    safeMatrix[0][0]
  );

  const fp = numberOrZero(
    safeMatrix[0][1]
  );

  const fn = numberOrZero(
    safeMatrix[1][0]
  );

  const tp = numberOrZero(
    safeMatrix[1][1]
  );

  return (
    <div className="matrix-card">
      <h3>{title}</h3>

      <div className="matrix">
        <div className="matrix-corner" />

        <div className="matrix-axis">
          Predicted Normal
        </div>

        <div className="matrix-axis">
          Predicted Anomaly
        </div>

        <div className="matrix-axis matrix-row-axis">
          Actual Normal
        </div>

        <div className="matrix-cell tn">
          <strong>
            {tn.toLocaleString("en-IN")}
          </strong>

          <span>TN</span>
        </div>

        <div className="matrix-cell fp">
          <strong>
            {fp.toLocaleString("en-IN")}
          </strong>

          <span>FP</span>
        </div>

        <div className="matrix-axis matrix-row-axis">
          Actual Anomaly
        </div>

        <div className="matrix-cell fn">
          <strong>
            {fn.toLocaleString("en-IN")}
          </strong>

          <span>FN</span>
        </div>

        <div className="matrix-cell tp">
          <strong>
            {tp.toLocaleString("en-IN")}
          </strong>

          <span>TP</span>
        </div>
      </div>
    </div>
  );
}

function ForecastEvaluationCard({
  title,
  bestModel,
  mae,
  rmse,
  mape,
}) {
  return (
    <div className="evaluation-card">
      <div className="evaluation-heading">
        <div>
          <span className="model-kicker">
            Forecast evaluation
          </span>

          <h3>{title}</h3>
        </div>

        <span className="winner-badge">
          {bestModel}
        </span>
      </div>

      <div className="evaluation-grid">
        <div>
          <span>MAE</span>

          <strong>
            {formatMoney(mae)}
          </strong>
        </div>

        <div>
          <span>RMSE</span>

          <strong>
            {formatMoney(rmse)}
          </strong>
        </div>

        <div>
          <span>MAPE</span>

          <strong>
            {formatPercent(mape)}
          </strong>
        </div>
      </div>
    </div>
  );
}

/*
 * Converts simple Markdown returned by Gemini
 * into readable React elements.
 *
 * Supported:
 * # Heading
 * ## Heading
 * ### Heading
 * - bullet
 * **bold**
 * ---
 */
function renderInlineMarkdown(text) {
  const parts = String(text).split(
    /(\*\*.*?\*\*)/g
  );

  return parts.map((part, index) => {
    if (
      part.startsWith("**") &&
      part.endsWith("**")
    ) {
      return (
        <strong key={index}>
          {part.slice(2, -2)}
        </strong>
      );
    }

    return <span key={index}>{part}</span>;
  });
}

function ReportContent({ report }) {
  if (!report) return null;

  const lines = String(report).split("\n");

  const elements = [];
  let bulletItems = [];

  function flushBullets() {
    if (bulletItems.length === 0) {
      return;
    }

    elements.push(
      <ul
        className="report-list"
        key={`list-${elements.length}`}
      >
        {bulletItems.map((item, index) => (
          <li key={index}>
            {renderInlineMarkdown(item)}
          </li>
        ))}
      </ul>
    );

    bulletItems = [];
  }

  lines.forEach((line, index) => {
    const trimmed = line.trim();

    if (!trimmed) {
      flushBullets();

      elements.push(
        <div
          className="report-spacer"
          key={`space-${index}`}
        />
      );

      return;
    }

    if (trimmed === "---") {
      flushBullets();

      elements.push(
        <hr
          className="report-divider"
          key={`hr-${index}`}
        />
      );

      return;
    }

    if (trimmed.startsWith("- ")) {
      bulletItems.push(
        trimmed.replace(/^-\s+/, "")
      );

      return;
    }

    flushBullets();

    if (trimmed.startsWith("### ")) {
      elements.push(
        <h4 key={`h4-${index}`}>
          {renderInlineMarkdown(
            trimmed.replace(/^###\s+/, "")
          )}
        </h4>
      );

      return;
    }

    if (trimmed.startsWith("## ")) {
      elements.push(
        <h3 key={`h3-${index}`}>
          {renderInlineMarkdown(
            trimmed.replace(/^##\s+/, "")
          )}
        </h3>
      );

      return;
    }

    if (trimmed.startsWith("# ")) {
      elements.push(
        <h2 key={`h2-${index}`}>
          {renderInlineMarkdown(
            trimmed.replace(/^#\s+/, "")
          )}
        </h2>
      );

      return;
    }

    elements.push(
      <p key={`p-${index}`}>
        {renderInlineMarkdown(trimmed)}
      </p>
    );
  });

  flushBullets();

  return (
    <div className="report-content">
      {elements}
    </div>
  );
}

function App() {
  const [dashboard, setDashboard] =
    useState(null);

  const [historical, setHistorical] =
    useState([]);

  const [forecast, setForecast] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [dashboardError, setDashboardError] =
    useState("");

  const [report, setReport] =
    useState("");

  const [reportLoading, setReportLoading] =
    useState(false);

  const [reportError, setReportError] =
    useState("");

  /*
   * ------------------------------------
   * LOAD DASHBOARD
   * ------------------------------------
   */
  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      setLoading(true);
      setDashboardError("");

      try {
        const payload = await fetchJSON(
          `${API_BASE_URL}/dashboard/`
        );

        if (cancelled) return;

        const normalizedDashboard =
          extractDashboard(payload);

        const normalizedHistorical =
          extractHistoricalData(payload);

        const normalizedForecast =
          extractForecastData(payload);
          
        console.log("Dashboard API response:", payload);
        console.log("Forecast data:", normalizedForecast);

        setDashboard(
          normalizedDashboard
        );

        setHistorical(
          normalizedHistorical
        );

        setForecast(
          normalizedForecast
        );
      } catch (error) {
        if (cancelled) return;

        console.error(
          "Dashboard API error:",
          error
        );

        setDashboardError(
          error.status
            ? `Dashboard request failed with status ${error.status}.`
            : "Unable to connect to the dashboard API."
        );
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadDashboard();

    return () => {
      cancelled = true;
    };
  }, []);

  /*
   * ------------------------------------
   * GENERATE AI REPORT
   * ------------------------------------
   */
  async function handleGenerateReport() {
    setReportLoading(true);
    setReportError("");

    try {
      const payload = await fetchJSON(
        `${API_BASE_URL}/report/`
      );

      const generatedReport =
        payload?.report ??
        payload?.data?.report ??
        payload?.text ??
        payload?.data?.text ??
        "";

      if (!generatedReport) {
        throw new Error(
          "The report response was empty."
        );
      }

      setReport(generatedReport);
    } catch (error) {
      console.error(
        "Report API error:",
        error
      );

      if (error.status === 403) {
        setReportError(
          "Report access was denied (403). The dashboard is working, but the backend report endpoint requires authentication or permission."
        );
      } else if (error.status) {
        setReportError(
          `Report request failed with status ${error.status}.`
        );
      } else {
        setReportError(
          "Unable to connect to the Gemini report endpoint."
        );
      }
    } finally {
      setReportLoading(false);
    }
  }

  /*
   * ------------------------------------
   * MODEL COMPARISON
   * ------------------------------------
   */
  const modelComparison = useMemo(() => {
    if (!dashboard) return [];

    return [
      {
        metric: "Precision",
        statistical:
          dashboard.statistical.precision,
        isolation:
          dashboard.isolation.precision,
      },

      {
        metric: "Recall",
        statistical:
          dashboard.statistical.recall,
        isolation:
          dashboard.isolation.recall,
      },

      {
        metric: "F1 Score",
        statistical:
          dashboard.statistical.f1,
        isolation:
          dashboard.isolation.f1,
      },
    ];
  }, [dashboard]);

  /*
   * ------------------------------------
   * LOADING SCREEN
   * ------------------------------------
   */
  if (loading) {
    return (
      <div className="app-shell">
        <div className="loading-screen">
          <div className="loading-spinner" />

          <h2>
            Loading financial analytics
          </h2>

          <p>
            Connecting to the Django API...
          </p>
        </div>
      </div>
    );
  }

  /*
   * ------------------------------------
   * ERROR SCREEN
   * ------------------------------------
   */
  if (dashboardError) {
    return (
      <div className="app-shell">
        <div className="error-screen">
          <div className="error-icon">
            !
          </div>

          <h2>
            Unable to load dashboard
          </h2>

          <p>{dashboardError}</p>

          <p className="error-help">
            Make sure Django is running at
            <code>
              {" "}
              http://127.0.0.1:8000/
            </code>
            .
          </p>
        </div>
      </div>
    );
  }

  const data = dashboard;

  return (
    <div className="app-shell">
      {/* -------------------------------- */}
      {/* HEADER */}
      {/* -------------------------------- */}

      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">
            AF
          </div>

          <div>
            <div className="brand-title">
              AI Finance System
            </div>

            <div className="brand-subtitle">
              Banking Analytics &
              Intelligent Monitoring
            </div>
          </div>
        </div>

        <div className="topbar-status">
          <span className="status-dot" />

          API Connected
        </div>
      </header>

      <main className="dashboard">
        {/* -------------------------------- */}
        {/* HERO */}
        {/* -------------------------------- */}

        <section className="hero">
          <div>
            <span className="hero-eyebrow">
              FINANCIAL INTELLIGENCE
            </span>

            <h1>
              Banking analytics dashboard
            </h1>

            <p>
              Verified analytics from the
              banking transaction dataset,
              anomaly models and
              chronological financial
              forecasting.
            </p>
          </div>

          <div className="hero-meta">
            <span>Dataset</span>

            <strong>
              2024–2025
            </strong>
          </div>
        </section>

        {/* -------------------------------- */}
        {/* SUMMARY CARDS */}
        {/* -------------------------------- */}

        <section className="metric-grid">
          <MetricCard
            label="Total Transactions"
            value={data.totalTransactions.toLocaleString(
              "en-IN"
            )}
            helper="Processed transactions"
            icon="↗"
            accent="blue"
          />

          <MetricCard
            label="Actual Anomalies"
            value={data.actualAnomalies.toLocaleString(
              "en-IN"
            )}
            helper={`${data.anomalyPercentage.toFixed(
              2
            )}% of transactions`}
            icon="!"
            accent="red"
          />

          <MetricCard
            label="Total Income"
            value={formatCompactMoney(
              data.totalIncome
            )}
            helper="2024–2025 dataset"
            icon="↑"
            accent="green"
          />

          <MetricCard
            label="Total Expense"
            value={formatCompactMoney(
              data.totalExpense
            )}
            helper="2024–2025 dataset"
            icon="↓"
            accent="purple"
          />
        </section>

        {/* -------------------------------- */}
        {/* HISTORICAL ANALYTICS */}
        {/* -------------------------------- */}

        <section className="section">
          <SectionHeader
            eyebrow="HISTORICAL ANALYTICS"
            title="Monthly income vs expense"
            description="Historical financial activity from January 2024 to December 2025."
          />

          <div className="chart-card">
            {historical.length > 0 ? (
              <div className="chart-wrapper">
                <ResponsiveContainer
                  width="100%"
                  height="100%"
                >
                  <LineChart
                    data={historical}
                    margin={{
                      top: 10,
                      right: 15,
                      left: 10,
                      bottom: 10,
                    }}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      vertical={false}
                    />

                    <XAxis
                      dataKey="month"
                      tick={{ fontSize: 12 }}
                      minTickGap={24}
                    />

                    <YAxis
                      tick={{ fontSize: 12 }}
                      tickFormatter={(value) =>
                        formatCompactMoney(
                          value
                        )
                      }
                    />

                    <Tooltip
                      formatter={(value) =>
                        formatMoney(value)
                      }
                      contentStyle={{
                        borderRadius: 12,
                        border:
                          "1px solid #e2e8f0",
                      }}
                    />

                    <Legend />

                    <Line
                      type="monotone"
                      dataKey="income"
                      name="Income"
                      stroke="#16a34a"
                      strokeWidth={3}
                      dot={false}
                      activeDot={{ r: 5 }}
                    />

                    <Line
                      type="monotone"
                      dataKey="expense"
                      name="Expense"
                      stroke="#ef4444"
                      strokeWidth={3}
                      dot={false}
                      activeDot={{ r: 5 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="empty-state">
                Historical monthly data is
                unavailable from the
                dashboard API.
              </div>
            )}
          </div>
        </section>

        {/* -------------------------------- */}
        {/* FORECAST */}
        {/* -------------------------------- */}

        <section className="section">
          <SectionHeader
            eyebrow="PREDICTIVE ANALYTICS"
            title="2026 financial forecast"
            description="Predicted monthly income and expense based on the selected forecasting model."
          />

          <div className="chart-card">
            {forecast.length > 0 ? (
              <div className="chart-wrapper">
                <ResponsiveContainer
                  width="100%"
                  height="100%"
                >
                  <LineChart
                    data={forecast}
                    margin={{
                      top: 10,
                      right: 15,
                      left: 10,
                      bottom: 10,
                    }}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      vertical={false}
                    />

                    <XAxis
                      dataKey="month"
                      tick={{ fontSize: 12 }}
                      minTickGap={20}
                    />

                    <YAxis
                      tick={{ fontSize: 12 }}
                      tickFormatter={(value) =>
                        formatCompactMoney(
                          value
                        )
                      }
                    />

                    <Tooltip
                      formatter={(value) =>
                        formatMoney(value)
                      }
                      contentStyle={{
                        borderRadius: 12,
                        border:
                          "1px solid #e2e8f0",
                      }}
                    />

                    <Legend />

                    <Line
                      type="monotone"
                      dataKey="income"
                      name="Predicted Income"
                      stroke="#2563eb"
                      strokeWidth={3}
                      dot={false}
                      activeDot={{ r: 5 }}
                    />

                    <Line
                      type="monotone"
                      dataKey="expense"
                      name="Predicted Expense"
                      stroke="#9333ea"
                      strokeWidth={3}
                      dot={false}
                      activeDot={{ r: 5 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="forecast-empty">
                <div className="forecast-empty-icon">
                  ◌
                </div>

                <h3>
                  Forecast chart unavailable
                </h3>

                <p>
                  The dashboard API did not
                  return monthly forecast
                  values.
                </p>
              </div>
            )}
          </div>
        </section>

        {/* -------------------------------- */}
        {/* ANOMALY DETECTION */}
        {/* -------------------------------- */}

        <section className="section">
          <SectionHeader
            eyebrow="ANOMALY DETECTION"
            title="Fraud detection performance"
            description="Statistical baseline compared with Isolation Forest."
          />

          <div className="model-grid">
            <ModelMetricCard
              title="Statistical Baseline"
              precision={
                data.statistical.precision
              }
              recall={
                data.statistical.recall
              }
              f1={
                data.statistical.f1
              }
              accent="model-blue"
            />

            <ModelMetricCard
              title="Isolation Forest"
              precision={
                data.isolation.precision
              }
              recall={
                data.isolation.recall
              }
              f1={data.isolation.f1}
              accent="model-purple"
            />
          </div>
        </section>

        {/* -------------------------------- */}
        {/* CONFUSION MATRIX */}
        {/* -------------------------------- */}

        <section className="section">
          <SectionHeader
            eyebrow="CLASSIFICATION DETAIL"
            title="Confusion matrix"
            description="Actual versus predicted anomaly classification."
          />

          <div className="matrix-grid">
            <ConfusionMatrix
              title="Statistical Baseline"
              matrix={
                data.statistical
                  .confusionMatrix
              }
            />

            <ConfusionMatrix
              title="Isolation Forest"
              matrix={
                data.isolation
                  .confusionMatrix
              }
            />
          </div>
        </section>

        {/* -------------------------------- */}
        {/* MODEL COMPARISON */}
        {/* -------------------------------- */}

        <section className="section">
          <SectionHeader
            eyebrow="MODEL COMPARISON"
            title="Fraud model comparison"
            description="Higher values indicate stronger performance for the supplied evaluation metrics."
          />

          <div className="chart-card">
            <div className="chart-wrapper chart-small">
              <ResponsiveContainer
                width="100%"
                height="100%"
              >
                <BarChart
                  data={modelComparison}
                  margin={{
                    top: 10,
                    right: 15,
                    left: 10,
                    bottom: 10,
                  }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    vertical={false}
                  />

                  <XAxis
                    dataKey="metric"
                    tick={{ fontSize: 12 }}
                  />

                  <YAxis
                    domain={[0, 100]}
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) =>
                      `${value}%`
                    }
                  />

                  <Tooltip
                    formatter={(value) =>
                      `${numberOrZero(
                        value
                      ).toFixed(2)}%`
                    }
                    contentStyle={{
                      borderRadius: 12,
                      border:
                        "1px solid #e2e8f0",
                    }}
                  />

                  <Legend />

                  <Bar
                    dataKey="isolation"
                    name="Isolation Forest"
                    fill="#7c3aed"
                    radius={[
                      6,
                      6,
                      0,
                      0,
                    ]}
                  />

                  <Bar
                    dataKey="statistical"
                    name="Statistical Baseline"
                    fill="#2563eb"
                    radius={[
                      6,
                      6,
                      0,
                      0,
                    ]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>

        {/* -------------------------------- */}
        {/* FORECAST EVALUATION */}
        {/* -------------------------------- */}

        <section className="section">
          <SectionHeader
            eyebrow="FORECAST EVALUATION"
            title="Chronological validation"
            description="Seasonal-Naive and SARIMA were evaluated using sequential historical periods."
          />

          <div className="evaluation-grid-main">
            <ForecastEvaluationCard
              title="Income Forecast"
              bestModel={
                data.incomeForecast
                  .bestModel
              }
              mae={
                data.incomeForecast.mae
              }
              rmse={
                data.incomeForecast.rmse
              }
              mape={
                data.incomeForecast.mape
              }
            />

            <ForecastEvaluationCard
              title="Expense Forecast"
              bestModel={
                data.expenseForecast
                  .bestModel
              }
              mae={
                data.expenseForecast.mae
              }
              rmse={
                data.expenseForecast.rmse
              }
              mape={
                data.expenseForecast.mape
              }
            />
          </div>
        </section>

        {/* -------------------------------- */}
        {/* SYSTEM INFORMATION */}
        {/* -------------------------------- */}

        <section className="section">
          <SectionHeader
            eyebrow="SYSTEM INFORMATION"
            title="Evaluation setup"
            description="Configuration used for the forecasting experiment."
          />

          <div className="system-grid">
            <div className="system-card">
              <span>
                Historical Months
              </span>

              <strong>
                {data.historicalMonths}
              </strong>
            </div>

            <div className="system-card">
              <span>
                Training Months
              </span>

              <strong>
                {data.trainingMonths}
              </strong>
            </div>

            <div className="system-card">
              <span>
                Validation Months
              </span>

              <strong>
                {data.validationMonths}
              </strong>
            </div>

            <div className="system-card">
              <span>
                Forecast Horizon
              </span>

              <strong>
                {data.forecastHorizon} Months
              </strong>
            </div>
          </div>
        </section>

        {/* -------------------------------- */}
        {/* AI MANAGEMENT REPORT */}
        {/* -------------------------------- */}

        <section className="section report-section">
          <SectionHeader
            eyebrow="GENERATIVE AI"
            title="AI management report"
            description="Verified financial analytics interpreted by Gemini AI."
          />

          <div className="report-card">
            <div className="report-toolbar">
              <div>
                <h3>
                  Management Analytics Report
                </h3>

                <p>
                  Gemini receives verified
                  application results and
                  produces the narrative
                  interpretation.
                </p>
              </div>

              <button
                className="report-button"
                onClick={
                  handleGenerateReport
                }
                disabled={reportLoading}
              >
                {reportLoading
                  ? "Generating..."
                  : "Generate AI Report"}
              </button>
            </div>

            {reportError && (
              <div className="report-error">
                <div className="report-error-title">
                  Unable to generate report
                </div>

                <p>{reportError}</p>
              </div>
            )}

            {report && (
              <ReportContent
                report={report}
              />
            )}
          </div>
        </section>
      </main>

      {/* -------------------------------- */}
      {/* FOOTER */}
      {/* -------------------------------- */}

      <footer className="footer">
        <div>
          <strong>
            AI Finance System
          </strong>

          <span>
            Banking Analytics &
            Intelligent Financial
            Monitoring
          </span>
        </div>

        <span>
          Research prototype • Synthetic
          data
        </span>
      </footer>
    </div>
  );
}

export default App;