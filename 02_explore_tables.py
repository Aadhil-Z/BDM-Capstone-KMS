# =====================================================================
#  02_explore_tables.py
#  Explore row counts, sample rows, and distinct reference values.
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
print("EXPLORING CAPSTONE TABLES")
print("=" * 60)

table_count_queries = {
    "person": """-- Count employee records.
        SELECT COUNT(*) FROM capstone.person""",
    "skill": """-- Count canonical skills.
        SELECT COUNT(*) FROM capstone.skill""",
    "project": """-- Count project records.
        SELECT COUNT(*) FROM capstone.project""",
    "person_skill": """-- Count person-to-skill relationships.
        SELECT COUNT(*) FROM capstone.person_skill""",
    "assignment": """-- Count person-to-project assignments.
        SELECT COUNT(*) FROM capstone.assignment""",
    "project_skill": """-- Count project-to-skill relationships.
        SELECT COUNT(*) FROM capstone.project_skill""",
    "interaction": """-- Count collaboration records.
        SELECT COUNT(*) FROM capstone.interaction""",
}
for table, query in table_count_queries.items():
    # Count rows in each core entity and relationship table.
    cursor.execute(query)
    print(f"{table}: {cursor.fetchone()[0]} rows")

for table in ["person", "skill"]:
    sample_query = {
        "person": """-- Preview at most five employee records.
            SELECT * FROM capstone.person LIMIT 5""",
        "skill": """-- Preview at most five skill definitions.
            SELECT * FROM capstone.skill LIMIT 5""",
    }[table]
    # Preview a small sample to inspect columns and representative values.
    cursor.execute(sample_query)
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    frame = pd.DataFrame(rows, columns=columns)
    print(f"\n{table} sample shape: {frame.shape}")
    print(frame)
    print(frame.dtypes)

# List distinct skill categories to inspect the available reference values.
cursor.execute(
    "-- List each distinct skill category in sorted order.\n"
    "SELECT DISTINCT category FROM capstone.skill ORDER BY category"
)
print(f"\nSkill categories: {[row[0] for row in cursor.fetchall()]}")
# List distinct project client types for the same reference-data check.
cursor.execute(
    "-- List each distinct project client type in sorted order.\n"
    "SELECT DISTINCT client_type FROM capstone.project ORDER BY client_type"
)
print(f"Project client types: {[row[0] for row in cursor.fetchall()]}")

cursor.close()
connection.close()
print("\nDone - connection closed.")
