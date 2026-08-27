# =====================================================================
#  03_aggregates.py
#  Run aggregate functions across people, skills, projects, and interactions.
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
print("AGGREGATE ANALYSIS")
print("=" * 60)

queries = [
    ("People per department", """
        SELECT department, COUNT(*) AS headcount
        FROM capstone.person GROUP BY department ORDER BY headcount DESC
    """),
    ("Average proficiency by skill category", """
        SELECT s.category, ROUND(AVG(ps.proficiency), 2) AS average_proficiency
        FROM capstone.person_skill ps JOIN capstone.skill s ON ps.skill_id = s.skill_id
        GROUP BY s.category ORDER BY s.category
    """),
    ("Interaction frequency by channel", """
        SELECT channel, SUM(frequency) AS total_frequency, ROUND(AVG(frequency), 2) AS average_frequency
        FROM capstone.interaction GROUP BY channel ORDER BY total_frequency DESC
    """),
    ("Projects by outcome", """
        SELECT outcome, COUNT(*) AS project_count
        FROM capstone.project GROUP BY outcome ORDER BY project_count DESC
    """),
]

for title, query in queries:
    print(f"\n{title}")
    cursor.execute(query)
    for row in cursor.fetchall():
        print(row)

cursor.execute(queries[0][1])
rows = cursor.fetchall()
columns = [description[0] for description in cursor.description]
department_frame = pd.DataFrame(rows, columns=columns)
print("\nDepartment headcount DataFrame:")
print(department_frame)
print(department_frame.dtypes)
print(f"Largest department: {department_frame.loc[department_frame['headcount'].idxmax(), 'department']}")

cursor.close()
connection.close()
print("\nDone - connection closed.")
