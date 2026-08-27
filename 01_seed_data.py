# =====================================================================
#  01_seed_data.py
#  Insert realistic sample data into every capstone table.
#  (Capstone: Organizational Knowledge Management System)
# =====================================================================

import psycopg2
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv(override=True)
DATABASE_URL = os.getenv("DATABASE_URL")

connection = psycopg2.connect(DATABASE_URL)
cursor = connection.cursor()

print("=" * 60)
print("SEEDING CAPSTONE DATA")
print("=" * 60)

people = [
    ("Aisha Khan", "aisha.khan@example.com", "Analytics", "Data Scientist", "2020-03-16"),
    ("Ben Carter", "ben.carter@example.com", "Engineering", "Backend Engineer", "2019-07-08"),
    ("Carla Mendes", "carla.mendes@example.com", "Product", "Product Manager", "2021-01-11"),
    ("Darius Lee", "darius.lee@example.com", "Engineering", "ML Engineer", "2022-05-23"),
    ("Elena Rossi", "elena.rossi@example.com", "Analytics", "BI Analyst", "2020-11-02"),
    ("Farah Ali", "farah.ali@example.com", "Product", "UX Researcher", "2018-09-17"),
    ("George Smith", "george.smith@example.com", "Engineering", "Cloud Architect", "2017-06-12"),
    ("Hana Ito", "hana.ito@example.com", "Analytics", "Data Engineer", "2023-02-06"),
    ("Ivan Petrov", "ivan.petrov@example.com", "Product", "Delivery Lead", "2019-04-29"),
    ("Julia Brown", "julia.brown@example.com", "Engineering", "Security Engineer", "2021-08-30"),
]
skills = [
    ("Python", "Technical", "Data Science"), ("SQL", "Technical", "Data"),
    ("Machine Learning", "Technical", "Data Science"), ("Cloud Architecture", "Technical", "Infrastructure"),
    ("Data Visualization", "Technical", "Analytics"), ("Cybersecurity", "Technical", "Security"),
    ("Project Management", "Soft", "Delivery"), ("Communication", "Soft", "Collaboration"),
    ("Leadership", "Soft", "Management"), ("User Research", "Soft", "Product"),
    ("Financial Modeling", "Domain", "Fintech"), ("Healthcare Compliance", "Domain", "Healthcare"),
    ("Retail Operations", "Domain", "Retail"), ("Risk Analysis", "Domain", "Fintech"),
    ("Process Design", "Domain", "Operations"),
]
projects = [
    ("Payments Fraud Detection", "Fintech", "2023-01-15", "2023-09-30", "Success", "Fintech"),
    ("Patient Portal Modernization", "Healthcare", "2022-04-01", "2023-02-28", "Success", "Healthcare"),
    ("Data Platform Migration", "Internal", "2024-01-08", "2024-10-31", "Success", "Internal"),
    ("Retail Demand Forecast", "Retail", "2024-03-01", "2024-08-15", "Success", "Retail"),
    ("Customer Insights Hub", "Retail", "2025-02-01", None, "Ongoing", "Retail"),
    ("Compliance Reporting Upgrade", "Fintech", "2021-06-01", "2022-01-31", "Success", "Internal"),
]
person_skills = [
    (1, 1, 5, "2026-05-01", 8), (1, 2, 5, "2026-04-20", 7), (1, 3, 5, "2026-05-10", 9), (1, 5, 4, "2025-11-01", 5), (1, 14, 4, "2024-08-10", 3),
    (2, 1, 4, "2025-06-12", 4), (2, 2, 5, "2026-03-18", 8), (2, 4, 5, "2024-12-01", 6), (2, 8, 4, "2026-02-12", 2),
    (3, 7, 5, "2026-06-01", 9), (3, 8, 5, "2026-05-15", 6), (3, 10, 4, "2025-07-20", 4),
    (4, 1, 5, "2026-04-11", 7), (4, 3, 5, "2026-04-25", 8), (4, 4, 4, "2025-03-10", 3), (4, 14, 4, "2025-02-01", 4),
    (5, 2, 5, "2026-01-19", 5), (5, 5, 5, "2026-02-14", 7), (5, 12, 3, "2023-08-01", 1),
    (6, 8, 5, "2026-05-02", 8), (6, 10, 5, "2026-05-22", 6), (6, 7, 3, "2024-01-10", 2),
    (7, 4, 5, "2026-03-01", 9), (7, 6, 5, "2026-04-01", 5), (7, 8, 4, "2025-10-01", 3),
    (8, 1, 4, "2026-05-03", 4), (8, 2, 5, "2026-05-05", 6), (8, 5, 4, "2026-03-20", 3),
    (9, 7, 5, "2026-04-30", 8), (9, 9, 5, "2025-12-01", 7), (9, 15, 4, "2024-05-01", 2),
    (10, 2, 4, "2025-09-01", 3), (10, 6, 5, "2026-02-20", 7), (10, 8, 3, "2023-04-15", 1),
]
assignments = [
    (1, 1, "Lead", "2023-01-15", "2023-09-30"), (2, 1, "Contributor", "2023-01-15", "2023-09-30"), (4, 1, "ML Engineer", "2023-03-01", "2023-09-30"),
    (3, 2, "Lead", "2022-04-01", "2023-02-28"), (6, 2, "UX Lead", "2022-05-01", "2023-02-28"), (10, 2, "Security Reviewer", "2022-06-01", "2023-02-28"),
    (2, 3, "Lead", "2024-01-08", "2024-10-31"), (7, 3, "Architect", "2024-01-08", "2024-10-31"), (8, 3, "Data Engineer", "2024-02-01", "2024-10-31"),
    (1, 4, "Analyst", "2024-03-01", "2024-08-15"), (5, 4, "Lead Analyst", "2024-03-01", "2024-08-15"), (9, 4, "Delivery Lead", "2024-03-01", "2024-08-15"),
    (3, 5, "Product Lead", "2025-02-01", None), (5, 5, "Analyst", "2025-02-01", None), (9, 5, "Program Lead", "2025-02-01", None),
    (9, 6, "Lead", "2021-06-01", "2022-01-31"), (10, 6, "Security Reviewer", "2021-06-01", "2022-01-31"),
]
project_skills = [
    (1, 1, "Required"), (1, 3, "Required"), (1, 14, "Required"), (1, 2, "Preferred"),
    (2, 2, "Required"), (2, 12, "Required"), (2, 10, "Preferred"),
    (3, 2, "Required"), (3, 4, "Required"), (3, 1, "Preferred"),
    (4, 3, "Required"), (4, 5, "Required"), (4, 2, "Preferred"),
    (5, 5, "Required"), (5, 10, "Required"), (5, 8, "Preferred"),
    (6, 2, "Required"), (6, 6, "Required"), (6, 14, "Preferred"),
]
interactions = [
    (1, 2, 1, "slack", 42, "2023-09-28"), (1, 4, 1, "meet", 18, "2023-09-25"), (2, 4, 1, "email", 27, "2023-09-29"),
    (3, 6, 2, "meet", 33, "2023-02-20"), (3, 10, 2, "email", 14, "2023-02-22"), (6, 10, 2, "slack", 21, "2023-02-24"),
    (2, 7, 3, "slack", 55, "2024-10-20"), (2, 8, 3, "email", 31, "2024-10-24"), (7, 8, 3, "meet", 26, "2024-10-15"),
    (1, 5, 4, "slack", 38, "2024-08-10"), (5, 9, 4, "meet", 17, "2024-08-12"), (1, 9, 4, "email", 19, "2024-08-14"),
    (3, 5, 5, "slack", 48, "2026-04-10"), (3, 9, 5, "meet", 20, "2026-04-12"), (5, 9, 5, "email", 16, "2026-04-15"),
    (9, 10, 6, "email", 29, "2022-01-20"), (3, 9, 6, "slack", 12, "2022-01-25"),
]

insertions = [
    ("person", "INSERT INTO capstone.person (name, email, department, role, joined_date) VALUES (%s, %s, %s, %s, %s)", people),
    ("skill", "INSERT INTO capstone.skill (name, category, domain) VALUES (%s, %s, %s)", skills),
    ("project", "INSERT INTO capstone.project (title, domain, start_date, end_date, outcome, client_type) VALUES (%s, %s, %s, %s, %s, %s)", projects),
    ("person_skill", "INSERT INTO capstone.person_skill (person_id, skill_id, proficiency, last_used_date, endorsement_count) VALUES (%s, %s, %s, %s, %s)", person_skills),
    ("assignment", "INSERT INTO capstone.assignment (person_id, project_id, role_played, from_date, to_date) VALUES (%s, %s, %s, %s, %s)", assignments),
    ("project_skill", "INSERT INTO capstone.project_skill (project_id, skill_id, importance) VALUES (%s, %s, %s)", project_skills),
    ("interaction", "INSERT INTO capstone.interaction (person_a, person_b, project_id, channel, frequency, last_contact) VALUES (%s, %s, %s, %s, %s, %s)", interactions),
]

for table_name, statement, rows in insertions:
    cursor.executemany(statement, rows)
    print(f"{table_name}: {len(rows)} rows seeded.")

connection.commit()

cursor.close()
connection.close()
print("\nDone - connection closed.")
