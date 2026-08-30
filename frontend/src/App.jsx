import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import "./App.css";

function App() {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const API_URL = "http://127.0.0.1:8000/api/dashboard/";

  useEffect(() => {
    fetch(API_URL, {
      credentials: "include",
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`API request failed: ${response.status}`);
        }

        return response.json();
      })
      .then((data) => {
        setDashboard(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="app">
        <div className="loading">
          <h2>AI Finance System</h2>
          <p>Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="app">
        <div className="error">
          <h2>Unable to load dashboard</h2>

          <p>{error}</p>

          <p>
            Make sure your Django backend is running on
            <strong> http://127.0.0.1:8000</strong>
          </p>

          <button
            type="button"
            onClick={() => window.location.reload()}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const summary = dashboard.summary;
  const fraud = dashboard.fraud_evaluation;
  const forecast = dashboard.forecast_evaluation;

  /*
   * Historical monthly data
   */
  const monthlyData = dashboard.monthly_trends.map((item) => ({
    month: item.month,
    income: item.income,
    expense: item.expense,
  }));

  /*
   * 2026 forecast data
   */
  const forecastData = dashboard.forecasts.map((item) => ({
    month: item.month,
    income: item.predicted_income,
    expense: item.predicted_expense,
  }));

  /*
   * Fraud model comparison
   */
  const fraudComparison = [
    {
      metric: "Precision",
      statistical:
        fraud.statistical_baseline.precision * 100,
      isolation:
        fraud.isolation_forest.precision * 100,
    },
    {
      metric: "Recall",
      statistical:
        fraud.statistical_baseline.recall * 100,
      isolation:
        fraud.isolation_forest.recall * 100,
    },
    {
      metric: "F1 Score",
      statistical:
        fraud.statistical_baseline.f1_score * 100,
      isolation:
        fraud.isolation_forest.f1_score * 100,
    },
  ];

  return (
    <div className="app">
      {/* ================================================== */}
      {/* HEADER */}
      {/* ================================================== */}

      <header className="header">
        <div>
          <h1>AI Finance System</h1>

          <p>
            Banking Analytics & Intelligent Financial Monitoring
          </p>
        </div>

        <div className="status">
          <span className="status-dot"></span>
          API Connected
        </div>
      </header>

      <main className="dashboard">

        {/* ================================================== */}
        {/* SUMMARY CARDS */}
        {/* ================================================== */}

        <section className="cards">

          <div className="card">
            <h3>Total Transactions</h3>

            <div className="value">
              {summary.total_transactions.toLocaleString()}
            </div>

            <p>Processed transactions</p>
          </div>

          <div className="card">
            <h3>Actual Anomalies</h3>

            <div className="value danger">
              {summary.actual_anomalies.toLocaleString()}
            </div>

            <p>
              {summary.anomaly_percentage}% of transactions
            </p>
          </div>

          <div className="card">
            <h3>Total Income</h3>

            <div className="value">
              ₹{summary.total_income.toLocaleString("en-IN", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </div>

            <p>2024–2025 dataset</p>
          </div>

          <div className="card">
            <h3>Total Expense</h3>

            <div className="value">
              ₹{summary.total_expense.toLocaleString("en-IN", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </div>

            <p>2024–2025 dataset</p>
          </div>

        </section>

        {/* ================================================== */}
        {/* HISTORICAL MONTHLY TREND */}
        {/* ================================================== */}

        <section className="panel">
          <h2>Monthly Income vs Expense</h2>

          <p className="chart-description">
            Historical financial activity from January 2024
            to December 2025
          </p>

          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" />

                <XAxis
                  dataKey="month"
                  interval={1}
                  angle={-35}
                  textAnchor="end"
                  height={70}
                />

                <YAxis
                  tickFormatter={(value) =>
                    `₹${(value / 1000000).toFixed(0)}M`
                  }
                />

                <Tooltip
                  formatter={(value) =>
                    `₹${Number(value).toLocaleString("en-IN", {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}`
                  }
                />

                <Legend />

                <Line
                  type="monotone"
                  dataKey="expense"
                  name="Expense"
                  strokeWidth={3}
                  dot={false}
                />

                <Line
                  type="monotone"
                  dataKey="income"
                  name="Income"
                  strokeWidth={3}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* ================================================== */}
        {/* 2026 FORECAST */}
        {/* ================================================== */}

        <section className="panel">
          <h2>2026 Financial Forecast</h2>

          <p className="chart-description">
            Predicted monthly income and expense for 2026
          </p>

          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={forecastData}>
                <CartesianGrid strokeDasharray="3 3" />

                <XAxis dataKey="month" />

                <YAxis
                  tickFormatter={(value) =>
                    `₹${(value / 1000000).toFixed(0)}M`
                  }
                />

                <Tooltip
                  formatter={(value) =>
                    `₹${Number(value).toLocaleString("en-IN", {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}`
                  }
                />

                <Legend />

                <Line
                  type="monotone"
                  dataKey="expense"
                  name="Predicted Expense"
                  strokeWidth={3}
                />

                <Line
                  type="monotone"
                  dataKey="income"
                  name="Predicted Income"
                  strokeWidth={3}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* ================================================== */}
        {/* FRAUD DETECTION PERFORMANCE */}
        {/* ================================================== */}

        <section className="panel">
          <h2>Fraud Detection Performance</h2>

          <div className="model-grid">

            {/* Statistical Baseline */}

            <div className="model">
              <h3>Statistical Baseline</h3>

              <div className="metric">
                <span>Precision</span>

                <strong>
                  {(
                    fraud.statistical_baseline.precision * 100
                  ).toFixed(2)}
                  %
                </strong>
              </div>

              <div className="metric">
                <span>Recall</span>

                <strong>
                  {(
                    fraud.statistical_baseline.recall * 100
                  ).toFixed(2)}
                  %
                </strong>
              </div>

              <div className="metric">
                <span>F1 Score</span>

                <strong>
                  {(
                    fraud.statistical_baseline.f1_score * 100
                  ).toFixed(2)}
                  %
                </strong>
              </div>
            </div>

            {/* Isolation Forest */}

            <div className="model highlight">
              <h3>Isolation Forest</h3>

              <div className="metric">
                <span>Precision</span>

                <strong>
                  {(
                    fraud.isolation_forest.precision * 100
                  ).toFixed(2)}
                  %
                </strong>
              </div>

              <div className="metric">
                <span>Recall</span>

                <strong>
                  {(
                    fraud.isolation_forest.recall * 100
                  ).toFixed(2)}
                  %
                </strong>
              </div>

              <div className="metric">
                <span>F1 Score</span>

                <strong>
                  {(
                    fraud.isolation_forest.f1_score * 100
                  ).toFixed(2)}
                  %
                </strong>
              </div>
            </div>

          </div>

          {/* ================================================== */}
          {/* CONFUSION MATRICES */}
          {/* ================================================== */}

          <div className="confusion-section">

            <h3>Confusion Matrix</h3>

            <div className="confusion-grid">

              {/* Statistical Baseline */}

              <div className="confusion-card">

                <h4>Statistical Baseline</h4>

                <table className="confusion-table">

                  <thead>
                    <tr>
                      <th></th>
                      <th>Predicted Normal</th>
                      <th>Predicted Anomaly</th>
                    </tr>
                  </thead>

                  <tbody>

                    <tr>
                      <th>Actual Normal</th>

                      <td className="true-negative">
                        49,500
                        <span>TN</span>
                      </td>

                      <td className="false-positive">
                        0
                        <span>FP</span>
                      </td>
                    </tr>

                    <tr>
                      <th>Actual Anomaly</th>

                      <td className="false-negative">
                        106
                        <span>FN</span>
                      </td>

                      <td className="true-positive">
                        394
                        <span>TP</span>
                      </td>
                    </tr>

                  </tbody>

                </table>

              </div>

              {/* Isolation Forest */}

              <div className="confusion-card">

                <h4>Isolation Forest</h4>

                <table className="confusion-table">

                  <thead>
                    <tr>
                      <th></th>
                      <th>Predicted Normal</th>
                      <th>Predicted Anomaly</th>
                    </tr>
                  </thead>

                  <tbody>

                    <tr>
                      <th>Actual Normal</th>

                      <td className="true-negative">
                        49,456
                        <span>TN</span>
                      </td>

                      <td className="false-positive">
                        44
                        <span>FP</span>
                      </td>
                    </tr>

                    <tr>
                      <th>Actual Anomaly</th>

                      <td className="false-negative">
                        58
                        <span>FN</span>
                      </td>

                      <td className="true-positive">
                        442
                        <span>TP</span>
                      </td>
                    </tr>

                  </tbody>

                </table>

              </div>

            </div>
          </div>
        </section>

        {/* ================================================== */}
        {/* FRAUD MODEL COMPARISON */}
        {/* ================================================== */}

        <section className="panel">

          <h2>Fraud Model Comparison</h2>

          <p className="chart-description">
            Comparison of statistical baseline and Isolation Forest
          </p>

          <div className="chart-wrapper">

            <ResponsiveContainer width="100%" height="100%">

              <BarChart data={fraudComparison}>

                <CartesianGrid strokeDasharray="3 3" />

                <XAxis dataKey="metric" />

                <YAxis
                  domain={[0, 100]}
                  tickFormatter={(value) => `${value}%`}
                />

                <Tooltip
                  formatter={(value) =>
                    `${Number(value).toFixed(2)}%`
                  }
                />

                <Legend />

                <Bar
                  dataKey="isolation"
                  name="Isolation Forest"
                />

                <Bar
                  dataKey="statistical"
                  name="Statistical Baseline"
                />

              </BarChart>

            </ResponsiveContainer>

          </div>

        </section>

        {/* ================================================== */}
        {/* FORECAST EVALUATION */}
        {/* ================================================== */}

        <section className="panel">

          <h2>Forecast Evaluation</h2>

          <div className="forecast-grid">

            {/* Income */}

            <div className="forecast-box">

              <h3>Income Forecast</h3>

              <p>
                Best Model:
                <strong>
                  {" "}
                  {forecast.income.best_model}
                </strong>
              </p>

              <p>
                MAE:
                <strong>
                  {" "}
                  ₹
                  {forecast.income.seasonal_naive.mae.toLocaleString(
                    "en-IN",
                    {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    }
                  )}
                </strong>
              </p>

              <p>
                RMSE:
                <strong>
                  {" "}
                  ₹
                  {forecast.income.seasonal_naive.rmse.toLocaleString(
                    "en-IN",
                    {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    }
                  )}
                </strong>
              </p>

              <p>
                MAPE:
                <strong>
                  {" "}
                  {forecast.income.seasonal_naive.mape}%
                </strong>
              </p>

            </div>

            {/* Expense */}

            <div className="forecast-box">

              <h3>Expense Forecast</h3>

              <p>
                Best Model:
                <strong>
                  {" "}
                  {forecast.expense.best_model}
                </strong>
              </p>

              <p>
                MAE:
                <strong>
                  {" "}
                  ₹
                  {forecast.expense.seasonal_naive.mae.toLocaleString(
                    "en-IN",
                    {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    }
                  )}
                </strong>
              </p>

              <p>
                RMSE:
                <strong>
                  {" "}
                  ₹
                  {forecast.expense.seasonal_naive.rmse.toLocaleString(
                    "en-IN",
                    {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    }
                  )}
                </strong>
              </p>

              <p>
                MAPE:
                <strong>
                  {" "}
                  {forecast.expense.seasonal_naive.mape}%
                </strong>
              </p>

            </div>

          </div>

        </section>

        {/* ================================================== */}
        {/* SYSTEM INFORMATION */}
        {/* ================================================== */}

        <section className="panel">

          <h2>System Information</h2>

          <div className="info-grid">

            <div>
              <span>Historical Months</span>
              <strong>
                {forecast.dataset.months}
              </strong>
            </div>

            <div>
              <span>Training Months</span>
              <strong>
                {forecast.dataset.training_months}
              </strong>
            </div>

            <div>
              <span>Validation Months</span>
              <strong>
                {forecast.dataset.validation_months}
              </strong>
            </div>

            <div>
              <span>Forecast Horizon</span>
              <strong>12 Months</strong>
            </div>

          </div>

        </section>

      </main>
    </div>
  );
}

export default App;