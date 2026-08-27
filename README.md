# Organizational Knowledge Management System

**Making dark data queryable.**

## Problem Statement

Organizations accumulate valuable knowledge in emails, chats, and project history, but this dark data is difficult to reuse. This project derives structured metadata from that history and combines it with skills and assignment records so managers can staff projects using evidence rather than gut feeling.

## ER Diagram (text)

```text
PERSON 1 -----< PERSON_SKILL >----- 1 SKILL
   |                                  |
   |                                  +-----< PROJECT_SKILL >----- PROJECT
   |                                                               |
   +-----< ASSIGNMENT >-------------------------------------------+
   |
   +-----< INTERACTION >-------------------------------------------+
```

## Schema: Table Summary

| Table | Description |
|---|---|
| `person` | Employees, departments, roles, and join dates. |
| `skill` | Canonical master list of technical, soft, and domain skills. |
| `project` | Completed and ongoing organizational projects. |
| `person_skill` | Person skills with proficiency, recency, and endorsements. |
| `assignment` | Historical project staffing, roles, and dates. |
| `project_skill` | Skills required or preferred by each project. |
| `interaction` | Derived collaboration metadata from email, Slack, and meetings. |

## Setup Instructions

1. Clone this repository and open the project directory.
2. Activate the existing virtual environment, or create one for the project.
3. Install dependencies:

   ```bash
   pip install psycopg2-binary python-dotenv pandas
   ```

4. Create a `.env` file in the repository root:

   ```text
   DATABASE_URL=your_supabase_connection_string
   ```

5. Run the scripts in order:

   ```bash
   python 00_create_schema.py
   python 01_seed_data.py
   python 02_explore_tables.py
   python 03_aggregates.py
   python 04_where_filters.py
   python 05_joins.py
   python 06_candidate_finder.py
   python 07_analytics.py
   ```

The schema script is intentionally resettable: it drops and recreates `capstone` for clean reruns.

## Script Reference

| Script | Purpose | Key concepts |
|---|---|---|
| `00_create_schema.py` | Create the schema and seven tables. | DDL, primary keys, foreign keys |
| `01_seed_data.py` | Insert realistic sample data. | Parameterized inserts, junction tables |
| `02_explore_tables.py` | Inspect counts, samples, and reference values. | SELECT, pandas DataFrames |
| `03_aggregates.py` | Summarize departments, skills, interactions, and outcomes. | COUNT, AVG, SUM, GROUP BY |
| `04_where_filters.py` | Filter data using business parameters. | WHERE, joins, date intervals |
| `05_joins.py` | Connect the system's core entities. | INNER JOIN, aliases, DataFrames |
| `06_candidate_finder.py` | Rank staffing candidates and find gaps. | Ranking, multi-table joins, subqueries |
| `07_analytics.py` | Produce deeper organizational insights. | HAVING, subqueries, coverage ratios |

## Key Business Queries

The main business logic lives in `06_candidate_finder.py`:

1. **Skill match ranking:** Given a skill, rank people by proficiency, recency, and endorsements.
2. **Multi-skill and domain match:** Find people with a target skill who have already worked in the target project domain.
3. **Skill gap detection:** For a project, identify required skills not held by any currently assigned person.

Together these queries turn scattered organizational history into an actionable staffing recommendation.

## Project Structure

```text
.
|-- .env
|-- 00_create_schema.py
|-- 01_seed_data.py
|-- 02_explore_tables.py
|-- 03_aggregates.py
|-- 04_where_filters.py
|-- 05_joins.py
|-- 06_candidate_finder.py
|-- 07_analytics.py
`-- README.md
```

## Tech Stack

- Python
- `psycopg2`
- `pandas`
- PostgreSQL
- Supabase
