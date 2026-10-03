# =====================================================================
#  05_joins.py
#  Demonstrate joins that connect people, skills, projects, and interactions.
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
print("JOIN ANALYSIS")
print("=" * 60)

queries = [
    ("Person-skill join", """
        -- Show each employee's catalog skills and proficiency.
        SELECT p.name, s.name AS skill, ps.proficiency
        FROM capstone.person p JOIN capstone.person_skill ps ON p.person_id = ps.person_id
        JOIN capstone.skill s ON ps.skill_id = s.skill_id
        ORDER BY p.name, ps.proficiency DESC
    """),
    ("Project-skill join", """
        -- Show each project's required or preferred catalog skills.
        SELECT proj.title, s.name AS skill, ps.importance
        FROM capstone.project proj JOIN capstone.project_skill ps ON proj.project_id = ps.project_id
        JOIN capstone.skill s ON ps.skill_id = s.skill_id ORDER BY proj.title, ps.importance
    """),
    ("Assignment history", """
        -- Show employee roles and dates for each assigned project.
        SELECT p.name, proj.title, a.role_played, a.from_date, a.to_date
        FROM capstone.person p JOIN capstone.assignment a ON p.person_id = a.person_id
        JOIN capstone.project proj ON a.project_id = proj.project_id ORDER BY a.from_date, p.name
    """),
    ("Collaboration network", """
        -- Show interaction participants, project, channel, and frequency.
        SELECT p1.name AS person_a, p2.name AS person_b, proj.title, i.channel, i.frequency
        FROM capstone.interaction i JOIN capstone.person p1 ON i.person_a = p1.person_id
        JOIN capstone.person p2 ON i.person_b = p2.person_id
        JOIN capstone.project proj ON i.project_id = proj.project_id ORDER BY i.frequency DESC
    """),
]

for index, (title, query) in enumerate(queries):
    print(f"\n{title}")
    # Join the related entity tables for the selected relationship report.
    cursor.execute(query)
    if index == 2:
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        assignment_frame = pd.DataFrame(rows, columns=columns)
        print(assignment_frame)
        print(f"Shape: {assignment_frame.shape}")
        print(assignment_frame.dtypes)
    else:
        for row in cursor.fetchall():
            print(row)

cursor.close()
connection.close()
print("\nDone - connection closed.")
