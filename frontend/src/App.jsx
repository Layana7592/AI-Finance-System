
import { useEffect, useState } from "react";
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

          <button onClick={() => window.location.reload()}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!dashboard) {
    return null;
  }

  const summary = dashboard.summary;
  const fraud = dashboard.fraud_evaluation;
  const forecast = dashboard.forecast_evaluation;

  return (
    <div className="app">

      {/* HEADER */}
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

        {/* SUMMARY CARDS */}
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
              ₹{summary.total_income.toLocaleString()}
            </div>
            <p>2024–2025 dataset</p>
          </div>

          <div className="card">
            <h3>Total Expense</h3>
            <div className="value">
              ₹{summary.total_expense.toLocaleString()}
            </div>
            <p>2024–2025 dataset</p>
          </div>

        </section>

        {/* FRAUD DETECTION */}
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

        {/* FORECAST EVALUATION */}
        <section className="panel">

          <h2>Forecast Evaluation</h2>

          <div className="forecast-grid">

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
                  ₹{forecast.income.seasonal_naive.mae.toLocaleString()}
                </strong>
              </p>

              <p>
                RMSE:
                <strong>
                  {" "}
                  ₹{forecast.income.seasonal_naive.rmse.toLocaleString()}
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
                  ₹{forecast.expense.seasonal_naive.mae.toLocaleString()}
                </strong>
              </p>

              <p>
                RMSE:
                <strong>
                  {" "}
                  ₹{forecast.expense.seasonal_naive.rmse.toLocaleString()}
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

        {/* SYSTEM INFORMATION */}
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
              <strong>
                12 Months
              </strong>
            </div>

          </div>

        </section>

      </main>

    </div>
  );
}

export default App;

