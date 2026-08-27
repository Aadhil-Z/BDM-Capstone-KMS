# =====================================================================
#  00_create_schema.py
#  Create the capstone schema and all tables from scratch.
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
print("CREATING CAPSTONE SCHEMA AND TABLES")
print("=" * 60)

statements = [
    ("person", """
        CREATE TABLE capstone.person (
            person_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            department VARCHAR(100),
            role VARCHAR(100),
            joined_date DATE
        )
    """),
    ("skill", """
        CREATE TABLE capstone.skill (
            skill_id SERIAL PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            category VARCHAR(50),
            domain VARCHAR(100)
        )
    """),
    ("project", """
        CREATE TABLE capstone.project (
            project_id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            domain VARCHAR(100),
            start_date DATE,
            end_date DATE,
            outcome VARCHAR(50),
            client_type VARCHAR(100)
        )
    """),
    ("person_skill", """
        CREATE TABLE capstone.person_skill (
            person_id INT NOT NULL REFERENCES capstone.person(person_id),
            skill_id INT NOT NULL REFERENCES capstone.skill(skill_id),
            proficiency INT CHECK (proficiency BETWEEN 1 AND 5),
            last_used_date DATE,
            endorsement_count INT DEFAULT 0,
            PRIMARY KEY (person_id, skill_id)
        )
    """),
    ("assignment", """
        CREATE TABLE capstone.assignment (
            assignment_id SERIAL PRIMARY KEY,
            person_id INT REFERENCES capstone.person(person_id),
            project_id INT REFERENCES capstone.project(project_id),
            role_played VARCHAR(100),
            from_date DATE,
            to_date DATE
        )
    """),
    ("project_skill", """
        CREATE TABLE capstone.project_skill (
            project_id INT NOT NULL REFERENCES capstone.project(project_id),
            skill_id INT NOT NULL REFERENCES capstone.skill(skill_id),
            importance VARCHAR(50),
            PRIMARY KEY (project_id, skill_id)
        )
    """),
    ("interaction", """
        CREATE TABLE capstone.interaction (
            interaction_id SERIAL PRIMARY KEY,
            person_a INT REFERENCES capstone.person(person_id),
            person_b INT REFERENCES capstone.person(person_id),
            project_id INT REFERENCES capstone.project(project_id),
            channel VARCHAR(50),
            frequency INT,
            last_contact DATE
        )
    """),
]

cursor.execute("""
    DROP SCHEMA IF EXISTS capstone CASCADE
""")
cursor.execute("""
    CREATE SCHEMA capstone
""")
connection.commit()
print("Schema capstone created.")

for table_name, statement in statements:
    cursor.execute(statement)
    connection.commit()
    print(f"Table capstone.{table_name} created.")

cursor.close()
connection.close()
print("\nDone - connection closed.")
