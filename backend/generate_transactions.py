import os
import random
from datetime import datetime, timedelta

import psycopg2
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL Connection

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

cursor = conn.cursor()

# Get Account IDs

cursor.execute("SELECT account_id FROM accounts")
account_ids = [row[0] for row in cursor.fetchall()]

if not account_ids:
    print("No accounts found.")
    exit()

# Date Range

start_date = datetime(2024, 1, 1)
end_date = datetime(2025, 12, 31)

# Transaction Categories

categories = {
    "Salary": {
        "amount": (30000, 90000),
        "merchants": ["Company Payroll", "Infosys Payroll", "TCS Payroll", "Wipro Payroll"]
    },
    "Shopping": {
        "amount": (300, 8000),
        "merchants": ["Amazon", "Flipkart", "Reliance", "DMart"]
    },
    "Fuel": {
        "amount": (500, 3000),
        "merchants": ["Indian Oil", "HPCL", "BPCL"]
    },
    "Electricity": {
        "amount": (1000, 6000),
        "merchants": ["KSEB"]
    },
    "Food": {
        "amount": (200, 2500),
        "merchants": ["Swiggy", "Zomato"]
    },
    "Medical": {
        "amount": (500, 15000),
        "merchants": ["Apollo Pharmacy", "MedPlus"]
    },
    "Travel": {
        "amount": (1000, 20000),
        "merchants": ["Uber", "Ola", "IRCTC"]
    },
    "Entertainment": {
        "amount": (300, 5000),
        "merchants": ["Netflix", "BookMyShow", "Amazon Prime"]
    },
    "ATM Withdrawal": {
        "amount": (500, 10000),
        "merchants": ["ATM"]
    },
    "UPI Transfer": {
        "amount": (100, 50000),
        "merchants": ["Google Pay", "PhonePe", "Paytm"]
    }
}

locations = [
    "Kannur",
    "Kochi",
    "Kozhikode",
    "Trivandrum",
    "Bangalore"
]

statuses = ["Success", "Success", "Success", "Pending", "Failed"]

print("Generating 50,000 realistic transactions...")

for _ in range(50000):

    account_id = random.choice(account_ids)

    transaction_type = random.choice(list(categories.keys()))

    minimum, maximum = categories[transaction_type]["amount"]

    amount = round(random.uniform(minimum, maximum), 2)

    merchant = random.choice(categories[transaction_type]["merchants"])

    location = random.choice(locations)

    random_days = random.randint(
        0,
        (end_date - start_date).days
    )

    transaction_time = start_date + timedelta(days=random_days)

    status = random.choice(statuses)

    # 2% Fraud Transactions
    if random.random() < 0.02:
        amount = round(random.uniform(150000, 500000), 2)
        merchant = "Unknown Merchant"
        status = "Success"

    cursor.execute("""
        INSERT INTO transactions
        (
            account_id,
            amount,
            transaction_type,
            merchant,
            location,
            transaction_time,
            status
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """,
    (
        account_id,
        amount,
        transaction_type,
        merchant,
        location,
        transaction_time,
        status
    ))

conn.commit()

print("50,000 transactions inserted successfully!")

cursor.close()
conn.close()