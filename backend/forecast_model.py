import os
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Load environment variables
load_dotenv()

# PostgreSQL connection
DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:"
    f"{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:"
    f"{os.getenv('DB_PORT')}/"
    f"{os.getenv('DB_NAME')}"
)

engine = create_engine(DATABASE_URL)

# Load Monthly Transaction Data

df = pd.read_csv("monthly_transactions.csv")

# Convert month column to datetime
df["month"] = pd.to_datetime(df["month"])

# Set month as index
df.set_index("month", inplace=True)

# Select total transaction amount
data = df["total_amount"]

print("Monthly Data:")
print(data)

# Train ARIMA Model

print("\nTraining ARIMA model...")

model = ARIMA(data, order=(1, 1, 1))
model_fit = model.fit()

print("Model trained successfully!")

# Forecast Next 12 Months

forecast = model_fit.forecast(steps=12)

forecast_dates = pd.date_range(
    start="2026-01-01",
    periods=12,
    freq="MS"
)

forecast_df = pd.DataFrame({
    "forecast_month": forecast_dates,
    "predicted_total_amount": forecast.values
})

# Prepare data for database
forecast_db = pd.DataFrame({
    "forecast_month": forecast_dates,
    "predicted_income": forecast.values,
    "predicted_expense": forecast.values * 0.70,   # Assume expenses are 70% of income
    "generated_at": datetime.now()
})

# Optional: Remove old forecasts before inserting new ones
with engine.begin() as conn:
    conn.exec_driver_sql("DELETE FROM financial_forecasts;")

# Save forecasts to PostgreSQL
forecast_db.to_sql(
    "financial_forecasts",
    engine,
    if_exists="append",
    index=False
)

print("\nForecast saved to financial_forecasts table successfully!")

print("\nForecast for 2026")
print(forecast_df)

# Plot

plt.figure(figsize=(12, 6))

plt.plot(
    data.index,
    data.values,
    label="Historical Data",
    marker="o"
)

plt.plot(
    forecast_dates,
    forecast.values,
    label="Forecast",
    marker="o"
)

plt.title("Financial Forecast using ARIMA")
plt.xlabel("Month")
plt.ylabel("Total Transaction Amount")
plt.legend()

plt.grid(True)

plt.show()
