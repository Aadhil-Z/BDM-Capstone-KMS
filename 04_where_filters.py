# =====================================================================
#  04_where_filters.py
#  Filter organizational knowledge with parameterized WHERE queries.
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
print("PARAMETERIZED WHERE FILTERS")
print("=" * 60)

filters = [
    ("Analytics people", "-- Select employees in the Analytics department.\nSELECT name, role FROM capstone.person WHERE department = %s", ("Analytics",)),
    ("Aisha's advanced skills", """
        -- List the named employee's skills with proficiency of at least four.
        SELECT s.name, ps.proficiency FROM capstone.person p
        JOIN capstone.person_skill ps ON p.person_id = ps.person_id
        JOIN capstone.skill s ON ps.skill_id = s.skill_id
        WHERE p.name = %s AND ps.proficiency >= 4
        ORDER BY ps.proficiency DESC, s.name
    """, ("Aisha Khan",)),
    ("Successful Fintech projects", """
        -- Return successful projects whose business domain is Fintech.
        SELECT title, domain, outcome FROM capstone.project
        WHERE domain = %s AND outcome = %s
    """, ("Fintech", "Success")),
    ("High-frequency Slack interactions", """
        -- Find Slack collaboration records above the supplied frequency threshold.
        SELECT person_a, person_b, frequency FROM capstone.interaction
        WHERE channel = %s AND frequency > %s
    """, ("slack", 30)),
    ("Skills unused in the last year", """
        -- Find employee skills whose last-use date is more than one year old.
        SELECT p.name, s.name AS skill, ps.last_used_date
        FROM capstone.person_skill ps
        JOIN capstone.person p ON ps.person_id = p.person_id
        JOIN capstone.skill s ON ps.skill_id = s.skill_id
        WHERE ps.last_used_date < NOW() - INTERVAL '1 year'
        ORDER BY ps.last_used_date
    """, ()),
]

for title, query, parameters in filters:
    print(f"\n{title}")
    # Apply the filter values as parameters rather than interpolating user values into SQL.
    cursor.execute(query, parameters)
    for row in cursor.fetchall():
        print(row)

cursor.close()
connection.close()
print("\nDone - connection closed.")
