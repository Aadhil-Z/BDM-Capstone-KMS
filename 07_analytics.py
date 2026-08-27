# =====================================================================
#  07_analytics.py
#  Run deeper analytics with grouping, HAVING, and subqueries.
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
print("DEEPER ANALYTICS")
print("=" * 60)

query_1 = """
    SELECT p.name, SUM(i.frequency) AS total_frequency
    FROM capstone.person p
    JOIN (
        SELECT person_a AS person_id, frequency FROM capstone.interaction
        UNION ALL
        SELECT person_b AS person_id, frequency FROM capstone.interaction
    ) i ON p.person_id = i.person_id
    GROUP BY p.name ORDER BY total_frequency DESC
"""
print("\nTop collaborators")
cursor.execute(query_1)
rows = cursor.fetchall()
columns = [description[0] for description in cursor.description]
collaborator_frame = pd.DataFrame(rows, columns=columns)
print(collaborator_frame)
print(f"Shape: {collaborator_frame.shape}")
print(collaborator_frame.dtypes)
print(collaborator_frame["total_frequency"].describe())

analytics_queries = [
    ("Skill versatility", """
        SELECT p.name, COUNT(DISTINCT s.category) AS category_count
        FROM capstone.person p JOIN capstone.person_skill ps ON p.person_id = ps.person_id
        JOIN capstone.skill s ON ps.skill_id = s.skill_id
        GROUP BY p.name HAVING COUNT(DISTINCT s.category) > 2
        ORDER BY category_count DESC, p.name
    """),
    ("Underutilized talent", """
        SELECT p.name, s.name AS highest_skill, ps.proficiency, ps.last_used_date
        FROM capstone.person p JOIN capstone.person_skill ps ON p.person_id = ps.person_id
        JOIN capstone.skill s ON ps.skill_id = s.skill_id
        WHERE ps.proficiency = (SELECT MAX(ps2.proficiency) FROM capstone.person_skill ps2 WHERE ps2.person_id = p.person_id)
          AND ps.last_used_date < NOW() - INTERVAL '1 year'
        ORDER BY ps.last_used_date
    """),
    ("Project required-skill coverage", """
        SELECT proj.title,
               COUNT(DISTINCT covered.skill_id) AS covered_required,
               COUNT(DISTINCT required.skill_id) AS total_required,
               ROUND(100.0 * COUNT(DISTINCT covered.skill_id) / NULLIF(COUNT(DISTINCT required.skill_id), 0), 2) AS coverage_percent
        FROM capstone.project proj
        LEFT JOIN capstone.project_skill required ON proj.project_id = required.project_id AND required.importance = 'Required'
        LEFT JOIN capstone.assignment a ON proj.project_id = a.project_id
        LEFT JOIN capstone.person_skill covered ON a.person_id = covered.person_id AND covered.skill_id = required.skill_id
        GROUP BY proj.project_id, proj.title ORDER BY proj.title
    """),
]

for title, query in analytics_queries:
    print(f"\n{title}")
    cursor.execute(query)
    for row in cursor.fetchall():
        print(row)

cursor.close()
connection.close()
print("\nDone - connection closed.")
