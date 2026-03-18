"""Create and populate the insurance.db SQLite database with fake policy data."""

import os
import random
import sqlite3
from datetime import timedelta

from faker import Faker

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "insurance.db")
NUM_POLICIES = 30

POLICY_TYPES = ["Auto", "Home", "Life", "Health"]
STATUSES = ["Active", "Expired", "Cancelled"]
STATUS_WEIGHTS = [0.6, 0.25, 0.15]

PREMIUM_RANGES = {
    "Auto": (600, 3000),
    "Home": (800, 4000),
    "Life": (300, 2000),
    "Health": (1500, 8000),
}

DEDUCTIBLE_RANGES = {
    "Auto": (250, 2000),
    "Home": (500, 5000),
    "Life": (0, 500),
    "Health": (500, 6000),
}

COVERAGE_LIMIT_RANGES = {
    "Auto": (25_000, 300_000),
    "Home": (100_000, 1_000_000),
    "Life": (50_000, 2_000_000),
    "Health": (100_000, 5_000_000),
}

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS policies (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_number   TEXT UNIQUE NOT NULL,
    holder_name     TEXT NOT NULL,
    holder_email    TEXT NOT NULL,
    policy_type     TEXT NOT NULL,
    premium         REAL NOT NULL,
    deductible      REAL NOT NULL,
    coverage_limit  REAL NOT NULL,
    start_date      TEXT NOT NULL,
    end_date        TEXT NOT NULL,
    status          TEXT NOT NULL
);
"""

INSERT_SQL = """
INSERT INTO policies (
    policy_number, holder_name, holder_email, policy_type,
    premium, deductible, coverage_limit, start_date, end_date, status
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""


def generate_policy_number(fake: Faker, index: int) -> str:
    prefix = fake.random_element(["POL", "INS", "COV"])
    return f"{prefix}-{2024_000 + index:07d}"


def build_policy(fake: Faker, index: int) -> tuple:
    policy_number = generate_policy_number(fake, index)
    holder_name = fake.name()
    holder_email = fake.email()
    policy_type = fake.random_element(POLICY_TYPES)
    status = random.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0]

    low, high = PREMIUM_RANGES[policy_type]
    premium = round(random.uniform(low, high), 2)

    low, high = DEDUCTIBLE_RANGES[policy_type]
    deductible = round(random.uniform(low, high), 2)

    low, high = COVERAGE_LIMIT_RANGES[policy_type]
    coverage_limit = round(random.uniform(low, high), 2)

    start_date = fake.date_between(start_date="-3y", end_date="today")
    end_date = start_date + timedelta(days=365)

    return (
        policy_number,
        holder_name,
        holder_email,
        policy_type,
        premium,
        deductible,
        coverage_limit,
        start_date.isoformat(),
        end_date.isoformat(),
        status,
    )


def main() -> None:
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing database: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(CREATE_TABLE_SQL)

    fake = Faker()
    Faker.seed(42)
    random.seed(42)

    policies = [build_policy(fake, i) for i in range(NUM_POLICIES)]
    cursor.executemany(INSERT_SQL, policies)
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM policies")
    count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT policy_type, COUNT(*) FROM policies GROUP BY policy_type ORDER BY policy_type"
    )
    breakdown = cursor.fetchall()

    cursor.execute(
        "SELECT status, COUNT(*) FROM policies GROUP BY status ORDER BY status"
    )
    status_breakdown = cursor.fetchall()

    conn.close()

    print(f"\nDatabase created at: {DB_PATH}")
    print(f"Total policies inserted: {count}\n")
    print("By type:")
    for ptype, cnt in breakdown:
        print(f"  {ptype:<10} {cnt}")
    print("\nBy status:")
    for status, cnt in status_breakdown:
        print(f"  {status:<12} {cnt}")


if __name__ == "__main__":
    main()
