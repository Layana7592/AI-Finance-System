import { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  BarChart,
  Bar,
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
            Make sure your Django backend is running on{" "}
            <strong>http://127.0.0.1:8000</strong>
          </p>
        </div>
      </div>
    );
  }

  const summary = dashboard.summary;
  const fraud = dashboard.fraud_evaluation;
  const forecast = dashboard.forecast_evaluation;

  /*
   * ========================================================
   * HISTORICAL DATA
   * ========================================================
   */

  const monthlyTrends = dashboard.monthly_trends || [];

  /*
   * ========================================================
   * 2026 FORECAST DATA
   * ========================================================
   */

  const forecasts = dashboard.forecasts || [];

  /*
   * ========================================================
   * FORMAT CURRENCY
   * ========================================================
   */

  const formatCurrency = (value) => {
    return `₹${Number(value).toLocaleString("en-IN", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  };

  /*
   * ========================================================
   * FORMAT CHART VALUES
   * ========================================================
   */

  const formatMillions = (value) => {
    return `₹${(value / 1000000).toFixed(0)}M`;
  };

  /*
   * ========================================================
   * FRAUD MODEL COMPARISON DATA
   * ========================================================
   */

  const fraudComparison = [
    {
      metric: "Precision",
      Statistical: fraud.statistical_baseline.precision * 100,
      "Isolation Forest": fraud.isolation_forest.precision * 100,
    },
    {
      metric: "Recall",
      Statistical: fraud.statistical_baseline.recall * 100,
      "Isolation Forest": fraud.isolation_forest.recall * 100,
    },
    {
      metric: "F1 Score",
      Statistical: fraud.statistical_baseline.f1_score * 100,
      "Isolation Forest": fraud.isolation_forest.f1_score * 100,
    },
  ];

  return (
    <div className="app">
      {/* ==================================================
          HEADER
          ================================================== */}

      <header className="header">
        <div>
          <h1>AI Finance System</h1>

          <p>Banking Analytics & Intelligent Financial Monitoring</p>
        </div>

        <div className="status">
          <span className="status-dot"></span>
          API Connected
        </div>
      </header>

      <main className="dashboard">
        {/* ==================================================
            SUMMARY CARDS
            ================================================== */}

        <section className="cards">
          <div className="card">
            <h3>Total Transactions</h3>

            <div className="value">
              {summary.total_transactions.toLocaleString("en-IN")}
            </div>

            <p>Processed transactions</p>
          </div>

          <div className="card">
            <h3>Actual Anomalies</h3>

            <div className="value danger">
              {summary.actual_anomalies.toLocaleString("en-IN")}
            </div>

            <p>{summary.anomaly_percentage}% of transactions</p>
          </div>

          <div className="card">
            <h3>Total Income</h3>

            <div className="value">
              {formatCurrency(summary.total_income)}
            </div>

            <p>2024–2025 dataset</p>
          </div>

          <div className="card">
            <h3>Total Expense</h3>

            <div className="value">
              {formatCurrency(summary.total_expense)}
            </div>

            <p>2024–2025 dataset</p>
          </div>
        </section>

        {/* ==================================================
            HISTORICAL CHART
            ================================================== */}

        <section className="panel chart-container">
          <h2>Monthly Income vs Expense</h2>

          <p className="chart-description">
            Historical financial activity from January 2024 to December 2025
          </p>

          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={monthlyTrends}
                margin={{
                  top: 20,
                  right: 30,
                  left: 20,
                  bottom: 10,
                }}
              >
                <CartesianGrid strokeDasharray="3 3" />

                <XAxis
                  dataKey="month"
                  tick={{ fontSize: 11 }}
                  interval={1}
                />

                <YAxis
                  tickFormatter={formatMillions}
                  tick={{ fontSize: 11 }}
                />

                <Tooltip
                  formatter={(value) => formatCurrency(value)}
                />

                <Legend />

                <Line
                  type="monotone"
                  dataKey="income"
                  name="Income"
                  stroke="#16a34a"
                  strokeWidth={3}
                  dot={{ r: 3 }}
                  activeDot={{ r: 6 }}
                />

                <Line
                  type="monotone"
                  dataKey="expense"
                  name="Expense"
                  stroke="#dc2626"
                  strokeWidth={3}
                  dot={{ r: 3 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* ==================================================
            2026 FORECAST CHART
            ================================================== */}

        <section className="panel chart-container">
          <h2>2026 Financial Forecast</h2>

          <p className="chart-description">
            Predicted monthly income and expense for 2026
          </p>

          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={forecasts}
                margin={{
                  top: 20,
                  right: 30,
                  left: 20,
                  bottom: 10,
                }}
              >
                <CartesianGrid strokeDasharray="3 3" />

                <XAxis
                  dataKey="month"
                  tick={{ fontSize: 11 }}
                />

                <YAxis
                  tickFormatter={formatMillions}
                  tick={{ fontSize: 11 }}
                />

                <Tooltip
                  formatter={(value) => formatCurrency(value)}
                />

                <Legend />

                <Line
                  type="monotone"
                  dataKey="predicted_income"
                  name="Predicted Income"
                  stroke="#2563eb"
                  strokeWidth={3}
                  dot={{ r: 4 }}
                  activeDot={{ r: 7 }}
                />

                <Line
                  type="monotone"
                  dataKey="predicted_expense"
                  name="Predicted Expense"
                  stroke="#f97316"
                  strokeWidth={3}
                  dot={{ r: 4 }}
                  activeDot={{ r: 7 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* ==================================================
            FRAUD DETECTION
            ================================================== */}

        <section className="panel">
          <h2>Fraud Detection Performance</h2>

          <div className="model-grid">
            <div className="model">
              <h3>Statistical Baseline</h3>

              <div className="metric">
                <span>Precision</span>

                <strong>
                  {(fraud.statistical_baseline.precision * 100).toFixed(2)}%
                </strong>
              </div>

              <div className="metric">
                <span>Recall</span>

                <strong>
                  {(fraud.statistical_baseline.recall * 100).toFixed(2)}%
                </strong>
              </div>

              <div className="metric">
                <span>F1 Score</span>

                <strong>
                  {(fraud.statistical_baseline.f1_score * 100).toFixed(2)}%
                </strong>
              </div>
            </div>

            <div className="model highlight">
              <h3>Isolation Forest</h3>

              <div className="metric">
                <span>Precision</span>

                <strong>
                  {(fraud.isolation_forest.precision * 100).toFixed(2)}%
                </strong>
              </div>

              <div className="metric">
                <span>Recall</span>

                <strong>
                  {(fraud.isolation_forest.recall * 100).toFixed(2)}%
                </strong>
              </div>

              <div className="metric">
                <span>F1 Score</span>

                <strong>
                  {(fraud.isolation_forest.f1_score * 100).toFixed(2)}%
                </strong>
              </div>
            </div>
          </div>
        </section>

        {/* ==================================================
            FRAUD MODEL CHART
            ================================================== */}

        <section className="panel chart-container">
          <h2>Fraud Model Comparison</h2>

          <p className="chart-description">
            Comparison of statistical baseline and Isolation Forest
          </p>

          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={fraudComparison}
                margin={{
                  top: 20,
                  right: 30,
                  left: 20,
                  bottom: 10,
                }}
              >
                <CartesianGrid strokeDasharray="3 3" />

                <XAxis dataKey="metric" />

                <YAxis
                  domain={[0, 100]}
                  tickFormatter={(value) => `${value}%`}
                />

                <Tooltip
                  formatter={(value) => `${Number(value).toFixed(2)}%`}
                />

                <Legend />

                <Bar
                  dataKey="Statistical"
                  name="Statistical Baseline"
                  fill="#64748b"
                  radius={[6, 6, 0, 0]}
                />

                <Bar
                  dataKey="Isolation Forest"
                  name="Isolation Forest"
                  fill="#2563eb"
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* ==================================================
            FORECAST EVALUATION
            ================================================== */}

        <section className="panel">
          <h2>Forecast Evaluation</h2>

          <div className="forecast-grid">
            <div className="forecast-box">
              <h3>Income Forecast</h3>

              <p>
                <span>Best Model</span>

                <strong>{forecast.income.best_model}</strong>
              </p>

              <p>
                <span>MAE</span>

                <strong>
                  {formatCurrency(forecast.income.seasonal_naive.mae)}
                </strong>
              </p>

              <p>
                <span>RMSE</span>

                <strong>
                  {formatCurrency(forecast.income.seasonal_naive.rmse)}
                </strong>
              </p>

              <p>
                <span>MAPE</span>

                <strong>
                  {forecast.income.seasonal_naive.mape}%
                </strong>
              </p>
            </div>

            <div className="forecast-box">
              <h3>Expense Forecast</h3>

              <p>
                <span>Best Model</span>

                <strong>{forecast.expense.best_model}</strong>
              </p>

              <p>
                <span>MAE</span>

                <strong>
                  {formatCurrency(forecast.expense.seasonal_naive.mae)}
                </strong>
              </p>

              <p>
                <span>RMSE</span>

                <strong>
                  {formatCurrency(forecast.expense.seasonal_naive.rmse)}
                </strong>
              </p>

              <p>
                <span>MAPE</span>

                <strong>
                  {forecast.expense.seasonal_naive.mape}%
                </strong>
              </p>
            </div>
          </div>
        </section>

        {/* ==================================================
            SYSTEM INFORMATION
            ================================================== */}

        <section className="panel">
          <h2>System Information</h2>

          <div className="info-grid">
            <div>
              <span>Historical Months</span>

              <strong>{forecast.dataset.months}</strong>
            </div>

            <div>
              <span>Training Months</span>

              <strong>{forecast.dataset.training_months}</strong>
            </div>

            <div>
              <span>Validation Months</span>

              <strong>{forecast.dataset.validation_months}</strong>
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