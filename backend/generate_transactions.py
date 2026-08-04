import os
import random
from datetime import datetime
from faker import Faker
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# PostgreSQL connection
conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

cursor = conn.cursor()

fake = Faker()

# Read existing account IDs
cursor.execute("SELECT account_id FROM accounts")
account_ids = [row[0] for row in cursor.fetchall()]

if not account_ids:
    print("No accounts found. Please insert accounts first.")
    conn.close()
    exit()

transaction_types = ["Credit", "Debit"]
statuses = ["Success", "Pending", "Failed"]

print("Generating 50,000 transactions...")

for _ in range(50000):
    account_id = random.choice(account_ids)
    amount = round(random.uniform(100, 100000), 2)
    transaction_type = random.choice(transaction_types)
    merchant = fake.company()
    location = fake.city()
    transaction_time = fake.date_time_between(start_date="-2y", end_date="now")
    status = random.choice(statuses)

    cursor.execute("""
        INSERT INTO transactions
        (account_id, amount, transaction_type, merchant,
         location, transaction_time, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (
        account_id,
        amount,
        transaction_type,
        merchant,
        location,
        transaction_time,
        status
    ))

conn.commit()

print("50,000 synthetic transactions inserted successfully!")

cursor.close()
conn.close()