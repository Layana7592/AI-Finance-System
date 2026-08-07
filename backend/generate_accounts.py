import random
from datetime import datetime
from faker import Faker
import psycopg2

fake = Faker()

# Database connection
conn = psycopg2.connect(
    host="localhost",
    database="fintech_db",
    user="postgres",
    password="postgres123"
)

cursor = conn.cursor()

print("Connected Successfully!")


# Get all users
cursor.execute("SELECT user_id FROM users;")
users = cursor.fetchall()

print("Total Users:", len(users))


account_count = 0


for user in users:

    user_id = user[0]

    # Every user gets savings account
    accounts = ["Savings"]

    # 50% users get current account also
    if random.random() < 0.5:
        accounts.append("Current")


    for acc_type in accounts:

        account_number = fake.bban()

        balance = round(random.uniform(5000, 100000), 2)

        cursor.execute(
            """
            INSERT INTO accounts
            (user_id, account_number, account_type, balance)
            VALUES (%s,%s,%s,%s)
            """,
            (
                user_id,
                account_number,
                acc_type,
                balance
            )
        )

        account_count += 1


conn.commit()

print("✅ Accounts Generated:", account_count)


cursor.close()
conn.close()