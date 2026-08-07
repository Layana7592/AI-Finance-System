from faker import Faker
from datetime import datetime
import random

from app.database import SessionLocal
from app.models import User

fake = Faker("en_IN")

db = SessionLocal()

EXISTING_USERS = db.query(User).count()

TOTAL_USERS = 500

USERS_TO_CREATE = TOTAL_USERS - EXISTING_USERS

print(f"Existing Users : {EXISTING_USERS}")
print(f"Generating {USERS_TO_CREATE} new users...\n")


for i in range(USERS_TO_CREATE):

    user = User(
        username=fake.unique.user_name(),
        email=fake.unique.email(),
        password_hash="hashed_password",
        role_id=random.randint(1, 4),
        branch_id=random.randint(1, 5),
        created_at=datetime.now()
    )

    db.add(user)

db.commit()

db.close()

print(f"✅ {USERS_TO_CREATE} users generated successfully!")