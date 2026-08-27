# =====================================================================
#  06_candidate_finder.py
#  Rank candidates and identify skill gaps for project staffing.
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
print("CANDIDATE FINDER")
print("=" * 60)

query_a = """
    SELECT p.name, ps.proficiency, ps.last_used_date, ps.endorsement_count
    FROM capstone.person p
    JOIN capstone.person_skill ps ON p.person_id = ps.person_id
    JOIN capstone.skill s ON ps.skill_id = s.skill_id
    WHERE s.name = %s
    ORDER BY ps.proficiency DESC, ps.last_used_date DESC
"""
print("\nQuery A - Python specialists")
cursor.execute(query_a, ("Python",))
for row in cursor.fetchall():
    print(row)

query_b = """
    SELECT p.name, ps.proficiency, COUNT(a.project_id) AS past_projects_in_domain
    FROM capstone.person p
    JOIN capstone.person_skill ps ON p.person_id = ps.person_id
    JOIN capstone.skill s ON ps.skill_id = s.skill_id
    JOIN capstone.assignment a ON p.person_id = a.person_id
    JOIN capstone.project proj ON a.project_id = proj.project_id
    WHERE s.name = %s AND proj.domain = %s
    GROUP BY p.name, ps.proficiency
    ORDER BY past_projects_in_domain DESC, ps.proficiency DESC
"""
print("\nQuery B - Python experience in Fintech")
cursor.execute(query_b, ("Python", "Fintech"))
rows = cursor.fetchall()
columns = [description[0] for description in cursor.description]
candidate_frame = pd.DataFrame(rows, columns=columns)
print(candidate_frame)
print(f"Shape: {candidate_frame.shape}")
print(candidate_frame.dtypes)

query_c = """
    SELECT s.name AS missing_skill, ps2.importance
    FROM capstone.project_skill ps2
    JOIN capstone.skill s ON ps2.skill_id = s.skill_id
    JOIN capstone.project proj ON ps2.project_id = proj.project_id
    WHERE proj.title = %s
      AND ps2.skill_id NOT IN (
          SELECT ps.skill_id
          FROM capstone.assignment a
          JOIN capstone.person_skill ps ON a.person_id = ps.person_id
          WHERE a.project_id = proj.project_id
      )
"""
print("\nQuery C - Missing skills for Payments Fraud Detection")
cursor.execute(query_c, ("Payments Fraud Detection",))
for row in cursor.fetchall():
    print(row)

cursor.close()
connection.close()
print("\nDone - connection closed.")
