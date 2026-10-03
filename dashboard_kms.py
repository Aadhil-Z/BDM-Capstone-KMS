"""Streamlit dashboard for browsing and managing the capstone KMS database."""

from contextlib import closing
from datetime import date, datetime
import os

from dotenv import load_dotenv
import pandas as pd
import psycopg2
import streamlit as st


load_dotenv(override=True)
DATABASE_URL = os.getenv("DATABASE_URL")

TABLES = {
    "People": {
        "table": "person",
        "keys": ["person_id"],
        "columns": ["person_id", "name", "email", "department", "role", "joined_date"],
        "browse_select": "src.name, src.email, src.department, src.role, src.joined_date",
        "browse_joins": "",
        "search": [
            "src.name", "src.email", "src.department", "src.role",
        ],
        "date": "joined_date",
        "fields": [
            ("name", "Name", "text", True),
            ("email", "Email", "text", True),
            ("department", "Department", "text_optional", False),
            ("role", "Role", "text_optional", False),
            ("joined_date", "Joined date", "date_optional", False),
        ],
    },
    "Skills": {
        "table": "skill",
        "keys": ["skill_id"],
        "columns": ["skill_id", "name", "category", "domain"],
        "browse_select": "src.name, src.category, src.domain",
        "browse_joins": "",
        "search": ["src.name", "src.category", "src.domain"],
        "date": None,
        "fields": [
            ("name", "Skill name", "text", True),
            ("category", "Category", "text_optional", False),
            ("domain", "Domain", "text_optional", False),
        ],
    },
    "Projects": {
        "table": "project",
        "keys": ["project_id"],
        "columns": [
            "project_id", "title", "domain", "start_date", "end_date",
            "outcome", "client_type",
        ],
        "browse_select": (
            "src.title, src.domain, src.start_date, src.end_date, "
            "src.outcome, src.client_type"
        ),
        "browse_joins": "",
        "search": ["src.title", "src.domain", "src.outcome", "src.client_type"],
        "date": "start_date",
        "fields": [
            ("title", "Title", "text", True),
            ("domain", "Domain", "text_optional", False),
            ("start_date", "Start date", "date_optional", False),
            ("end_date", "End date", "date_optional", False),
            ("outcome", "Outcome", "text_optional", False),
            ("client_type", "Client type", "text_optional", False),
        ],
    },
    "Person skills": {
        "table": "person_skill",
        "keys": ["person_id", "skill_id"],
        "columns": [
            "person_id", "skill_id", "proficiency", "last_used_date",
            "endorsement_count",
        ],
        "browse_select": (
            "p.name AS person, s.name AS skill, src.proficiency, "
            "src.last_used_date, src.endorsement_count"
        ),
        "browse_joins": (
            " LEFT JOIN capstone.person p ON p.person_id = src.person_id"
            " LEFT JOIN capstone.skill s ON s.skill_id = src.skill_id"
        ),
        "search": [
            "CAST(src.person_id AS TEXT)",
            "CAST(src.skill_id AS TEXT)",
            "(SELECT p.name FROM capstone.person p WHERE p.person_id = src.person_id)",
            "(SELECT s.name FROM capstone.skill s WHERE s.skill_id = src.skill_id)",
        ],
        "date": "last_used_date",
        "fields": [
            ("person_id", "Person", "person", True),
            ("skill_id", "Skill", "skill", True),
            ("proficiency", "Proficiency (1–5)", "proficiency", True),
            ("last_used_date", "Last used date", "date_optional", False),
            ("endorsement_count", "Endorsements", "count", True),
        ],
    },
    "Assignments": {
        "table": "assignment",
        "keys": ["assignment_id"],
        "columns": [
            "assignment_id", "person_id", "project_id", "role_played",
            "from_date", "to_date",
        ],
        "browse_select": (
            "p.name AS person, proj.title AS project, src.role_played, "
            "src.from_date, src.to_date"
        ),
        "browse_joins": (
            " LEFT JOIN capstone.person p ON p.person_id = src.person_id"
            " LEFT JOIN capstone.project proj ON proj.project_id = src.project_id"
        ),
        "search": [
            "src.role_played",
            "CAST(src.person_id AS TEXT)",
            "CAST(src.project_id AS TEXT)",
            "(SELECT p.name FROM capstone.person p WHERE p.person_id = src.person_id)",
            "(SELECT proj.title FROM capstone.project proj WHERE proj.project_id = src.project_id)",
        ],
        "date": "from_date",
        "fields": [
            ("person_id", "Person", "person", True),
            ("project_id", "Project", "project", True),
            ("role_played", "Role played", "text_optional", False),
            ("from_date", "From date", "date_optional", False),
            ("to_date", "To date", "date_optional", False),
        ],
    },
    "Project skills": {
        "table": "project_skill",
        "keys": ["project_id", "skill_id"],
        "columns": ["project_id", "skill_id", "importance"],
        "browse_select": (
            "proj.title AS project, s.name AS skill, src.importance"
        ),
        "browse_joins": (
            " LEFT JOIN capstone.project proj ON proj.project_id = src.project_id"
            " LEFT JOIN capstone.skill s ON s.skill_id = src.skill_id"
        ),
        "search": [
            "src.importance",
            "(SELECT proj.title FROM capstone.project proj WHERE proj.project_id = src.project_id)",
            "(SELECT s.name FROM capstone.skill s WHERE s.skill_id = src.skill_id)",
        ],
        "date": None,
        "fields": [
            ("project_id", "Project", "project", True),
            ("skill_id", "Skill", "skill", True),
            ("importance", "Importance", "text", True),
        ],
    },
    "Interactions": {
        "table": "interaction",
        "keys": ["interaction_id"],
        "columns": [
            "interaction_id", "person_a", "person_b", "project_id",
            "channel", "frequency", "last_contact",
        ],
        "browse_select": (
            "pa.name AS person_a, pb.name AS person_b, proj.title AS project, "
            "src.channel, src.frequency, src.last_contact"
        ),
        "browse_joins": (
            " LEFT JOIN capstone.person pa ON pa.person_id = src.person_a"
            " LEFT JOIN capstone.person pb ON pb.person_id = src.person_b"
            " LEFT JOIN capstone.project proj ON proj.project_id = src.project_id"
        ),
        "search": [
            "src.channel",
            "CAST(src.person_a AS TEXT)",
            "CAST(src.person_b AS TEXT)",
            "CAST(src.project_id AS TEXT)",
            "(SELECT p.name FROM capstone.person p WHERE p.person_id = src.person_a)",
            "(SELECT p.name FROM capstone.person p WHERE p.person_id = src.person_b)",
            "(SELECT proj.title FROM capstone.project proj WHERE proj.project_id = src.project_id)",
        ],
        "date": "last_contact",
        "fields": [
            ("person_a", "Person A", "person", True),
            ("person_b", "Person B", "person", True),
            ("project_id", "Project", "project", True),
            ("channel", "Channel", "text_optional", False),
            ("frequency", "Interaction frequency", "count", True),
            ("last_contact", "Last contact", "date_optional", False),
        ],
    },
}


def _read_frame(query, parameters=()):
    """Run a read-only parameterized query and return its rows as a DataFrame."""
    with closing(psycopg2.connect(DATABASE_URL)) as connection, connection:
        with connection.cursor() as cursor:
            cursor.execute(query, parameters)
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
    return pd.DataFrame(rows, columns=columns)


def _write(query, parameters):
    """Run one data-changing statement in a transaction."""
    with closing(psycopg2.connect(DATABASE_URL)) as connection, connection:
        with connection.cursor() as cursor:
            cursor.execute(query, parameters)


def _filter_parts(config, search_text="", date_range=None):
    """Build parameterized search and date filters from table allowlists."""
    conditions = []
    parameters = []

    search_columns = config["search"]
    if search_text.strip() and search_columns:
        conditions.append(
            "(" + " OR ".join(f"CAST({column} AS TEXT) ILIKE %s" for column in search_columns) + ")"
        )
        parameters.extend([f"%{search_text.strip()}%"] * len(search_columns))

    date_column = config["date"]
    if date_column and date_range:
        start_date, end_date = date_range
        conditions.append(f"src.{date_column} BETWEEN %s AND %s")
        parameters.extend([start_date, end_date])

    return conditions, parameters


def _table_frame(config, search_text="", date_range=None):
    """Select one table's editable columns using allowlisted filters."""
    conditions, parameters = _filter_parts(config, search_text, date_range)
    query = (
        "SELECT " + ", ".join(config["columns"])
        + f" FROM capstone.{config['table']} AS src"
    )
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY " + ", ".join(f"src.{key}" for key in config["keys"])
    return _read_frame(query, parameters)


def _browse_frame(config, search_text="", date_range=None):
    """Select readable business labels by joining normalized relationship tables."""
    conditions, parameters = _filter_parts(config, search_text, date_range)
    query = (
        "SELECT " + config["browse_select"]
        + f" FROM capstone.{config['table']} AS src"
        + config["browse_joins"]
    )
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY " + ", ".join(f"src.{key}" for key in config["keys"])
    return _read_frame(query, parameters)
def _lookup_options(entity):
    """Read IDs and human-readable labels for foreign-key dropdowns."""
    if entity == "person":
        # Populate foreign-key dropdowns with selectable people and departments.
        frame = _read_frame(
            "SELECT person_id, name, email, department FROM capstone.person ORDER BY name"
        )
        return {
            int(row.person_id): (
                f"{row.name} · {row.department or 'No department'} · {row.email}"
            )
            for row in frame.itertuples(index=False)
        }
    if entity == "skill":
        # Populate the skill relationship dropdown with canonical catalog entries.
        frame = _read_frame(
            "SELECT skill_id, name, category FROM capstone.skill ORDER BY name"
        )
        return {
            int(row.skill_id): f"{row.name} · {row.category or 'Uncategorized'}"
            for row in frame.itertuples(index=False)
        }
    if entity == "project":
        # Populate the project relationship dropdown with readable project titles.
        frame = _read_frame(
            "SELECT project_id, title, domain FROM capstone.project ORDER BY title"
        )
        return {
            int(row.project_id): f"{row.title} · {row.domain or 'No domain'}"
            for row in frame.itertuples(index=False)
        }
    raise ValueError(f"Unsupported lookup entity: {entity}")


def _as_date(value):
    if value is None or pd.isna(value):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return pd.to_datetime(value).date()


def _render_field(field, label, kind, required, value, key):
    """Render a typed editor widget and convert its value for PostgreSQL."""
    label = label or field.replace("_", " ").title()
    if kind in {"person", "skill", "project"}:
        options = _lookup_options(kind)
        allow_empty = not required
        choices = ([None] if allow_empty else []) + list(options)
        current = int(value) if value is not None and not pd.isna(value) else None
        if current not in choices and choices:
            current = choices[0]
        selected = st.selectbox(
            label,
            choices,
            index=choices.index(current) if choices else None,
            format_func=lambda item: (
                "— Not selected —" if item is None else options[item]
            ),
            key=key,
            disabled=not choices,
        )
        return selected

    if kind == "date_optional":
        current = _as_date(value)
        has_date = st.checkbox(
            f"Set {label.lower()}",
            value=current is not None,
            key=f"{key}_enabled",
        )
        if not has_date:
            return None
        return st.date_input(
            label,
            value=current or date.today(),
            key=key,
        )

    if kind == "proficiency":
        current = 1 if value is None or pd.isna(value) else int(value)
        return st.slider(label, min_value=1, max_value=5, value=current, key=key)

    if kind == "count":
        current = 0 if value is None or pd.isna(value) else int(value)
        return st.number_input(
            label, min_value=0, step=1, value=current, key=key
        )

    current = "" if value is None or pd.isna(value) else str(value)
    if kind == "text_optional":
        text = st.text_input(label, value=current, key=key)
        return text.strip() or None
    text = st.text_input(label, value=current, key=key)
    return text.strip()


def _manage_table(page, config, frame):
    """Render create, edit, and guarded delete controls for a table."""
    st.subheader(f"Manage {page.lower()}")
    fields = config["fields"]
    keys = config["keys"]
    lookup_maps = {
        "person": _lookup_options("person"),
        "skill": _lookup_options("skill"),
        "project": _lookup_options("project"),
    }
    records = [
        {
            column: value.item() if hasattr(value, "item") else value
            for column, value in row._asdict().items()
        }
        for row in frame.itertuples(index=False)
    ]
    base_labels = [
        _format_managed_record(config["table"], record, lookup_maps)
        for record in records
    ]
    label_counts = {label: base_labels.count(label) for label in base_labels}
    occurrences = {}
    labels = []
    for label in base_labels:
        occurrences[label] = occurrences.get(label, 0) + 1
        labels.append(
            f"{label} · entry {occurrences[label]}"
            if label_counts[label] > 1 else label
        )
    selected_label = st.selectbox(
        "Select a record to edit or delete",
        ["— Select a record —"] + labels,
        key=f"{config['table']}_selected_record",
    )
    selected_index = None
    if records and selected_label != "— Select a record —":
        selected_index = labels.index(selected_label)
    selected = records[selected_index] if selected_index is not None else None

    with st.expander(f"Add {page.lower().rstrip('s')}", expanded=False):
        with st.form(f"create_{config['table']}"):
            values = {}
            for field, label, kind, required in fields:
                values[field] = _render_field(
                    field, label, kind, required, None,
                    f"create_{config['table']}_{field}",
                )
            create_submitted = st.form_submit_button("Create record")
        if create_submitted:
            missing = [
                label for field, label, _, required in fields
                if required and (values[field] is None or values[field] == "")
            ]
            if missing:
                st.error("Complete required fields: " + ", ".join(missing))
            else:
                # Insert only the table's allowlisted editable columns.
                columns = [field[0] for field in fields]
                placeholders = ", ".join(["%s"] * len(columns))
                query = (
                    f"INSERT INTO capstone.{config['table']} "
                    f"({', '.join(columns)}) VALUES ({placeholders})"
                )
                try:
                    _write(query, [values[column] for column in columns])
                    st.success("Record created.")
                    st.rerun()
                except psycopg2.Error as error:
                    st.error(f"Could not create record: {error}")

    if selected is None:
        st.info("Select a record above to edit or delete it. Database constraints are enforced.")
        return

    record_token = "_".join(str(selected[column]) for column in keys)
    editable_fields = [field for field in fields if field[0] not in keys]
    with st.form(f"edit_{config['table']}_{record_token}"):
        updated = {}
        for field, label, kind, required in editable_fields:
            updated[field] = _render_field(
                field, label, kind, required, selected[field],
                f"edit_{config['table']}_{record_token}_{field}",
            )
        save_submitted = st.form_submit_button("Save changes")
    if save_submitted:
        missing = [
            label for field, label, _, required in editable_fields
            if required and (updated[field] is None or updated[field] == "")
        ]
        if missing:
            st.error("Complete required fields: " + ", ".join(missing))
        elif not editable_fields:
            st.info("This record has no editable non-key fields.")
        else:
            # Update only non-key fields and target the selected primary-key value(s).
            assignments = ", ".join(f"{field} = %s" for field in updated)
            key_filter = " AND ".join(f"{column} = %s" for column in keys)
            query = (
                f"UPDATE capstone.{config['table']} SET {assignments} "
                f"WHERE {key_filter}"
            )
            parameters = list(updated.values()) + [selected[column] for column in keys]
            try:
                _write(query, parameters)
                st.success("Record updated.")
                st.rerun()
            except psycopg2.Error as error:
                st.error(f"Could not update record: {error}")

    st.warning(
        "Deleting is permanent. If other rows reference this record, PostgreSQL will block the delete."
    )
    confirm_delete = st.checkbox(
        "I understand this will permanently delete the selected record.",
        key=f"confirm_delete_{config['table']}_{record_token}",
    )
    if st.button(
        "Delete selected record",
        type="secondary",
        disabled=not confirm_delete,
        key=f"delete_{config['table']}_{record_token}",
    ):
        # Delete exactly the selected record; foreign keys protect referenced rows.
        key_filter = " AND ".join(f"{column} = %s" for column in keys)
        query = f"DELETE FROM capstone.{config['table']} WHERE {key_filter}"
        try:
            _write(query, [selected[column] for column in keys])
            st.success("Record deleted.")
            st.rerun()
        except psycopg2.Error as error:
            st.error(f"Could not delete record: {error}")


def _format_managed_record(table, record, lookups):
    """Build a human-readable record label without exposing foreign-key IDs."""
    if table == "person":
        return f"{record['name']} · {record['email']}"
    if table == "skill":
        category = record["category"] or "Uncategorized"
        return f"{record['name']} · {category}"
    if table == "project":
        domain = record["domain"] or "Domain not recorded"
        return f"{record['title']} · {domain}"
    if table == "person_skill":
        return (
            f"{lookups['person'].get(record['person_id'], 'Unknown person')} · "
            f"{lookups['skill'].get(record['skill_id'], 'Unknown skill')}"
        )
    if table == "assignment":
        role = record["role_played"] or "Role not recorded"
        return (
            f"{lookups['person'].get(record['person_id'], 'Unknown person')} · "
            f"{lookups['project'].get(record['project_id'], 'Unknown project')} · "
            f"{role} · {record['from_date'] or 'Start date not recorded'}"
        )
    if table == "project_skill":
        return (
            f"{lookups['project'].get(record['project_id'], 'Unknown project')} · "
            f"{lookups['skill'].get(record['skill_id'], 'Unknown skill')} · "
            f"{record['importance']}"
        )
    if table == "interaction":
        return (
            f"{lookups['person'].get(record['person_a'], 'Unknown person')} ↔ "
            f"{lookups['person'].get(record['person_b'], 'Unknown person')} · "
            f"{lookups['project'].get(record['project_id'], 'Unknown project')} · "
            f"{record['last_contact'] or 'Date not recorded'}"
        )
    return "Record"


def _show_people_dashboard():
    """Show a searchable people directory and joined employee skill profiles."""
    st.header("People")
    st.write(
        "Choose a person to see their service history, skill profile, assignments, "
        "and recorded collaboration in one place."
    )

    department_values = _read_frame(
        """
        -- Provide department filters while retaining employees with no department.
        SELECT DISTINCT department
        FROM capstone.person
        ORDER BY department NULLS LAST
        """
    )["department"].tolist()
    filters = st.columns([2, 1, 1])
    search_text = filters[0].text_input(
        "Search people, roles, or skills",
        placeholder="Name, email, role, department, or skill",
        key="people_search",
    )
    normalized_departments = list(dict.fromkeys(
        department if department is not None else "Not recorded"
        for department in department_values
    ))
    department_options = ["All departments", *normalized_departments]
    selected_department = filters[1].selectbox(
        "Department",
        department_options,
        key="people_department_filter",
    )
    use_joined_filter = filters[2].checkbox(
        "Filter join date",
        key="people_joined_filter",
    )

    joined_range = None
    if use_joined_filter:
        date_columns = st.columns(2)
        joined_start = date_columns[0].date_input(
            "Joined from",
            date(date.today().year - 40, 1, 1),
            key="people_joined_from",
        )
        joined_end = date_columns[1].date_input(
            "Joined to",
            date.today(),
            key="people_joined_to",
        )
        if joined_start > joined_end:
            st.error("The beginning join date must be before the end date.")
            st.stop()
        joined_range = (joined_start, joined_end)

    people = _read_frame(
        """
        -- Combine people with pre-aggregated skill names and assignment counts.
        WITH skill_summary AS (
            SELECT ps.person_id,
                   string_agg(s.name, ', ' ORDER BY s.name) AS skills
            FROM capstone.person_skill ps
            JOIN capstone.skill s ON s.skill_id = ps.skill_id
            GROUP BY ps.person_id
        ),
        assignment_summary AS (
            SELECT person_id, COUNT(*) AS project_count
            FROM capstone.assignment
            GROUP BY person_id
        )
        SELECT p.person_id, p.name, p.email, p.department, p.role,
               p.joined_date,
               ROUND(EXTRACT(EPOCH FROM age(CURRENT_DATE, p.joined_date)) /
                     (365.25 * 24 * 60 * 60), 1) AS years_of_service,
               COALESCE(ss.skills, 'No recorded skills') AS skills,
               COALESCE(ass.project_count, 0) AS project_count
        FROM capstone.person p
        LEFT JOIN skill_summary ss ON ss.person_id = p.person_id
        LEFT JOIN assignment_summary ass ON ass.person_id = p.person_id
        WHERE (%s = '' OR CONCAT_WS(' ', p.name, p.email, p.department, p.role,
                                     ss.skills) ILIKE %s)
          AND (%s = TRUE OR COALESCE(p.department, 'Not recorded') = %s)
          AND (%s = TRUE OR p.joined_date BETWEEN %s AND %s)
        ORDER BY p.name, p.email
        """,
        (
            search_text.strip(),
            f"%{search_text.strip()}%",
            selected_department == "All departments",
            selected_department,
            joined_range is None,
            joined_range[0] if joined_range else None,
            joined_range[1] if joined_range else None,
        ),
    )
    st.caption(f"{len(people)} employee(s) match these filters.")
    if people.empty:
        st.info("No employees match the selected search and filters.")
        return

    # IDs are retained only for internal selection; the displayed directory omits them.
    st.dataframe(
        people.drop(columns=["person_id"]),
        hide_index=True,
        width="stretch",
    )
    person_labels = {
        int(row.person_id): (
            f"{row.name} · {row.department or 'No department'} · "
            f"{row.role or 'Role not recorded'} · {row.email}"
        )
        for row in people.itertuples(index=False)
    }
    person_ids = list(person_labels)
    selected_person_id = st.selectbox(
        "Open person profile",
        person_ids,
        format_func=lambda person_id: person_labels[person_id],
        key="person_profile_selector",
    )
    _show_person_profile(selected_person_id)


def _show_person_profile(person_id):
    """Show joined skill scores, service time, assignments, and collaboration."""
    profile = _read_frame(
        """
        -- Summarize one person's service, skills, endorsements, and assignments.
        WITH skill_summary AS (
            SELECT person_id, COUNT(*) AS skill_count,
                   ROUND(AVG(proficiency)::numeric, 2) AS average_proficiency,
                   SUM(endorsement_count) AS endorsements
            FROM capstone.person_skill
            WHERE person_id = %s
            GROUP BY person_id
        ),
        assignment_summary AS (
            SELECT person_id, COUNT(*) AS project_count
            FROM capstone.assignment
            WHERE person_id = %s
            GROUP BY person_id
        )
        SELECT p.person_id, p.name, p.email, p.department, p.role,
               p.joined_date,
               EXTRACT(YEAR FROM age(CURRENT_DATE, p.joined_date))::int
                   AS service_years,
               EXTRACT(MONTH FROM age(CURRENT_DATE, p.joined_date))::int
                   AS service_months,
               COALESCE(ss.skill_count, 0) AS skill_count,
               ss.average_proficiency,
               COALESCE(ss.endorsements, 0) AS endorsements,
               COALESCE(a.project_count, 0) AS project_count
        FROM capstone.person p
        LEFT JOIN skill_summary ss ON ss.person_id = p.person_id
        LEFT JOIN assignment_summary a ON a.person_id = p.person_id
        WHERE p.person_id = %s
        """,
        (person_id, person_id, person_id),
    )
    if profile.empty:
        st.warning("The selected person is no longer in the database.")
        return
    person = profile.iloc[0]

    st.divider()
    st.subheader(f"Profile: {person['name']}")
    st.caption(
        " · ".join(
            str(value)
            for value in (person["role"], person["department"], person["email"])
            if value
        )
    )
    service_label = (
        f"{int(person['service_years'])}y {int(person['service_months'])}m"
        if person["joined_date"] is not None and not pd.isna(person["joined_date"])
        else "Not recorded"
    )
    metrics = st.columns(5)
    metrics[0].metric("Service period", service_label)
    metrics[1].metric("Skills recorded", int(person["skill_count"]))
    metrics[2].metric(
        "Average proficiency",
        (
            f"{float(person['average_proficiency']):.2f} / 5"
            if not pd.isna(person["average_proficiency"])
            else "No skills recorded"
        ),
    )
    metrics[3].metric("Endorsements", int(person["endorsements"]))
    metrics[4].metric("Project assignments", int(person["project_count"]))
    st.caption(
        "Service period is calculated from the join date through today. Average proficiency "
        "is the equally weighted arithmetic mean of that person's recorded 1–5 ratings."
    )

    skills = _read_frame(
        """
        -- Join a person's recorded skills to their proficiency and recency details.
        SELECT s.name AS skill, s.category, s.domain,
               ps.proficiency, ps.last_used_date, ps.endorsement_count
        FROM capstone.person_skill ps
        JOIN capstone.skill s ON s.skill_id = ps.skill_id
        WHERE ps.person_id = %s
        ORDER BY ps.proficiency DESC, ps.endorsement_count DESC, s.name
        """,
        (person_id,),
    )
    project_history = _read_frame(
        """
        -- Show named projects and employee roles in date order.
        SELECT proj.title AS project, proj.domain, a.role_played,
               a.from_date, a.to_date,
               CASE
                   WHEN a.from_date IS NULL THEN 'Dates incomplete'
                   WHEN a.from_date > CURRENT_DATE THEN 'Scheduled'
                   WHEN a.to_date IS NULL OR a.to_date >= CURRENT_DATE THEN 'Active'
                   ELSE 'Completed'
               END AS status
        FROM capstone.assignment a
        JOIN capstone.project proj ON proj.project_id = a.project_id
        WHERE a.person_id = %s
        ORDER BY a.from_date DESC NULLS LAST, proj.title
        """,
        (person_id,),
    )
    collaboration = _read_frame(
        """
        -- Resolve the employee's interaction links to collaborator and project names.
        SELECT DISTINCT other.name AS collaborator, proj.title AS project,
               i.channel, i.frequency, i.last_contact
        FROM capstone.interaction i
        JOIN capstone.person other
          ON other.person_id = CASE
              WHEN i.person_a = %s THEN i.person_b ELSE i.person_a
          END
        LEFT JOIN capstone.project proj ON proj.project_id = i.project_id
        WHERE i.person_a = %s OR i.person_b = %s
        ORDER BY i.last_contact DESC NULLS LAST, other.name
        """,
        (person_id, person_id, person_id),
    )

    skill_column, history_column = st.columns([1, 1])
    with skill_column:
        st.markdown("**Skill scores**")
        st.caption(
            "Proficiency is the stored 1–5 rating (the schema does not record who assessed it). "
            "Endorsements and last-used dates are supporting signals, not part of the score."
        )
        if skills.empty:
            st.info("No skills have been recorded for this person.")
        else:
            st.bar_chart(
                skills.set_index("skill")[["proficiency"]],
                horizontal=True,
            )
            st.dataframe(skills, hide_index=True, width="stretch")
    with history_column:
        st.markdown("**Project history**")
        if project_history.empty:
            st.info("No project assignments have been recorded.")
        else:
            st.dataframe(project_history, hide_index=True, width="stretch")

    st.markdown("**Collaboration history**")
    if collaboration.empty:
        st.info("No collaboration records have been recorded for this person.")
    else:
        st.dataframe(collaboration, hide_index=True, width="stretch")


def _show_projects_dashboard():
    """Show readable project records, team assignments, and skill coverage."""
    st.header("Projects")
    st.write(
        "Browse projects with named team members and skill coverage. The IDs needed "
        "to join normalized tables stay behind the scenes."
    )
    filters = st.columns([2, 1])
    search_text = filters[0].text_input(
        "Search projects, domains, skills, or team members",
        key="project_search",
    )
    use_date_filter = filters[1].checkbox(
        "Filter project start dates",
        key="project_date_filter",
    )
    date_range = None
    if use_date_filter:
        date_columns = st.columns(2)
        start_date = date_columns[0].date_input(
            "Starts from",
            date(date.today().year - 20, 1, 1),
            key="project_start_from",
        )
        end_date = date_columns[1].date_input(
            "Starts to",
            date.today(),
            key="project_start_to",
        )
        if start_date > end_date:
            st.error("The beginning date must be before the ending date.")
            st.stop()
        date_range = (start_date, end_date)

    projects = _read_frame(
        """
        -- Join project metadata to readable team, skill, and coverage summaries.
        WITH team AS (
            SELECT a.project_id,
                   string_agg(DISTINCT p.name, ', ' ORDER BY p.name) AS team_members
            FROM capstone.assignment a
            JOIN capstone.person p ON p.person_id = a.person_id
            GROUP BY a.project_id
        ),
        required AS (
            SELECT ps.project_id, ps.skill_id, s.name AS skill
            FROM capstone.project_skill ps
            JOIN capstone.skill s ON s.skill_id = ps.skill_id
            WHERE ps.importance ILIKE 'required'
        ),
        coverage AS (
            SELECT r.project_id,
                   COUNT(DISTINCT r.skill_id) AS required_count,
                   COUNT(DISTINCT r.skill_id) FILTER (
                       WHERE EXISTS (
                           SELECT 1
                           FROM capstone.assignment a
                           JOIN capstone.person_skill held
                             ON held.person_id = a.person_id
                           WHERE a.project_id = r.project_id
                             AND held.skill_id = r.skill_id
                       )
                   ) AS covered_count,
                   string_agg(DISTINCT r.skill, ', ' ORDER BY r.skill)
                       AS required_skills
            FROM required r
            GROUP BY r.project_id
        )
        SELECT proj.project_id, proj.title, proj.domain, proj.start_date,
               proj.end_date, proj.outcome, proj.client_type,
               COALESCE(team.team_members, 'No team recorded') AS team_members,
               COALESCE(coverage.required_count, 0) AS required_skill_count,
               COALESCE(coverage.covered_count, 0) AS covered_skill_count,
               CASE
                   WHEN COALESCE(coverage.required_count, 0) = 0 THEN NULL
                   ELSE ROUND(
                       100.0 * coverage.covered_count / coverage.required_count, 1
                   )
               END AS required_skill_coverage,
               COALESCE(coverage.required_skills, 'No required skills recorded')
                   AS required_skills
        FROM capstone.project proj
        LEFT JOIN team ON team.project_id = proj.project_id
        LEFT JOIN coverage ON coverage.project_id = proj.project_id
        WHERE (%s = '' OR CONCAT_WS(' ', proj.title, proj.domain, proj.outcome,
                                     proj.client_type, team.team_members,
                                     coverage.required_skills) ILIKE %s)
          AND (%s = TRUE OR proj.start_date BETWEEN %s AND %s)
        ORDER BY proj.start_date DESC NULLS LAST, proj.title
        """,
        (
            search_text.strip(),
            f"%{search_text.strip()}%",
            date_range is None,
            date_range[0] if date_range else None,
            date_range[1] if date_range else None,
        ),
    )
    projects["required_skill_coverage"] = pd.to_numeric(
        projects["required_skill_coverage"], errors="coerce"
    )
    st.caption(f"{len(projects)} project(s) match these filters.")
    if projects.empty:
        st.info("No projects match this search and date range.")
        return

    st.dataframe(
        projects.drop(columns=["project_id"]),
        hide_index=True,
        width="stretch",
    )
    project_labels = {
        int(row.project_id): (
            f"{row.title} · {row.domain or 'No domain'} · "
            f"{row.start_date or 'Start not recorded'}"
        )
        for row in projects.itertuples(index=False)
    }
    project_id = st.selectbox(
        "Open project profile",
        list(project_labels),
        format_func=lambda selected_id: project_labels[selected_id],
        key="project_profile_selector",
    )
    project = projects.loc[projects["project_id"] == project_id].iloc[0]
    st.subheader(f"Project profile: {project['title']}")
    metrics = st.columns(4)
    metrics[0].metric("Domain", project["domain"] or "Not recorded")
    metrics[1].metric("Status", project["outcome"] or "Not recorded")
    metrics[2].metric(
        "Required skills covered",
        (
            f"{int(project['covered_skill_count'])} / {int(project['required_skill_count'])}"
            if int(project["required_skill_count"]) else "No requirements"
        ),
    )
    metrics[3].metric(
        "Coverage",
        (
            f"{float(project['required_skill_coverage']):.1f}%"
            if not pd.isna(project["required_skill_coverage"]) else "Not applicable"
        ),
    )

    detail_columns = st.columns(2)
    with detail_columns[0]:
        st.markdown("**Required skill coverage**")
        skill_coverage = _read_frame(
            """
            -- Show each required skill and whether any assigned person holds it.
            SELECT s.name AS skill,
                   CASE WHEN EXISTS (
                       SELECT 1
                       FROM capstone.assignment a
                       JOIN capstone.person_skill held
                         ON held.person_id = a.person_id
                       WHERE a.project_id = ps.project_id
                         AND held.skill_id = ps.skill_id
                   ) THEN 'Covered' ELSE 'Uncovered' END AS coverage,
                   COUNT(DISTINCT held.person_id) AS assigned_holders
            FROM capstone.project_skill ps
            JOIN capstone.skill s ON s.skill_id = ps.skill_id
            LEFT JOIN capstone.assignment a ON a.project_id = ps.project_id
            LEFT JOIN capstone.person_skill held
              ON held.person_id = a.person_id AND held.skill_id = ps.skill_id
            WHERE ps.project_id = %s AND ps.importance ILIKE 'required'
            GROUP BY ps.project_id, ps.skill_id, s.name
            ORDER BY coverage, s.name
            """,
            (project_id,),
        )
        if skill_coverage.empty:
            st.info("No required project skills have been recorded.")
        else:
            st.dataframe(skill_coverage, hide_index=True, width="stretch")
    with detail_columns[1]:
        st.markdown("**Assigned team**")
        team = _read_frame(
            """
            -- Show each assigned employee with role, dates, and skill summary.
            SELECT p.name AS person, p.department, p.role AS job_title,
                   a.role_played, a.from_date, a.to_date,
                   COALESCE(skills.skill_list, 'No skills recorded') AS skills
            FROM capstone.assignment a
            JOIN capstone.person p ON p.person_id = a.person_id
            LEFT JOIN LATERAL (
                SELECT string_agg(s.name, ', ' ORDER BY s.name) AS skill_list
                FROM capstone.person_skill ps
                JOIN capstone.skill s ON s.skill_id = ps.skill_id
                WHERE ps.person_id = p.person_id
            ) skills ON TRUE
            WHERE a.project_id = %s
            ORDER BY p.name
            """,
            (project_id,),
        )
        if team.empty:
            st.info("No team assignments have been recorded.")
        else:
            st.dataframe(team, hide_index=True, width="stretch")


def _show_overview():
    """Display headline metrics and charts across the normalized ERD."""
    # Count people for the overview KPI.
    people = _read_frame("SELECT COUNT(*) AS total FROM capstone.person").iloc[0, 0]
    # Count projects for the overview KPI.
    projects = _read_frame("SELECT COUNT(*) AS total FROM capstone.project").iloc[0, 0]
    # Count catalog entries for the overview KPI.
    skills = _read_frame("SELECT COUNT(*) AS total FROM capstone.skill").iloc[0, 0]
    # Count person-to-project assignments for the overview KPI.
    assignments = _read_frame(
        "SELECT COUNT(*) AS total FROM capstone.assignment"
    ).iloc[0, 0]
    columns = st.columns(4)
    for column, label, value in zip(
        columns,
        ["People", "Projects", "Skills", "Assignments"],
        [people, projects, skills, assignments],
    ):
        column.metric(label, int(value))

    left, right = st.columns(2)
    with left:
        # Aggregate employee headcount by department for the comparison chart.
        departments = _read_frame(
            """
            -- Count people by department, including records without a department.
            SELECT COALESCE(department, 'Not recorded') AS department,
                   COUNT(*) AS people
            FROM capstone.person
            GROUP BY department
            ORDER BY people DESC, department
            """
        )
        st.subheader("People by department")
        if not departments.empty:
            st.bar_chart(departments.set_index("department"))
        else:
            st.info("No people records found.")
    with right:
        # Aggregate project counts by outcome for the comparison chart.
        outcomes = _read_frame(
            """
            -- Count projects by outcome, including records without an outcome.
            SELECT COALESCE(outcome, 'Not recorded') AS outcome,
                   COUNT(*) AS projects
            FROM capstone.project
            GROUP BY outcome
            ORDER BY projects DESC, outcome
            """
        )
        st.subheader("Projects by outcome")
        if not outcomes.empty:
            st.bar_chart(outcomes.set_index("outcome"))
        else:
            st.info("No project records found.")

    st.subheader("Skills held across the organization")
    # Count distinct people holding each catalog skill, retaining unused skills.
    skill_counts = _read_frame(
        """
        -- Show organization-wide skill prevalence, including skills held by nobody.
        SELECT s.name AS skill, COUNT(DISTINCT ps.person_id) AS people
        FROM capstone.skill s
        LEFT JOIN capstone.person_skill ps ON ps.skill_id = s.skill_id
        GROUP BY s.skill_id, s.name
        ORDER BY people DESC, s.name
        """
    )
    if not skill_counts.empty:
        st.bar_chart(skill_counts.head(15).set_index("skill"))


def _show_insights():
    """Display talent utilization, collaboration, and project skill coverage."""
    st.header("Talent and collaboration insights")
    with st.expander("How these insights are built"):
        st.markdown(
            """
            This app reads the existing normalized `capstone` tables. It does **not**
            create a denormalized reporting table or a separate star schema. The insight
            queries use PostgreSQL CTEs (`WITH ...`) as temporary, query-time steps:

            - **Underutilized-candidate signal:** CTEs identify recent assignments and
              strong but stale skills, then select people with no assignment in the lookback.
            - **Top collaborators:** a CTE turns the two participant columns into one
              participant list, then sums recorded interaction frequency per person.
            - **Project skill coverage:** CTEs collect required skills and count each
              requirement as covered when at least one assigned person has that skill.

            These are decision-support signals, not a utilization score or a staffing
            recommendation. Coverage checks whether a skill is recorded for an assigned
            person; it does not assess proficiency thresholds, availability, or recency.
            """
        )
        st.code(
            """WITH intermediate_result AS (
    SELECT ...
    FROM normalized_tables
    JOIN related_tables ON foreign_key_match
)
SELECT grouped_metrics
FROM intermediate_result
GROUP BY business_entity;""",
            language="sql",
        )

    window = st.selectbox(
        "Activity lookback window",
        [90, 180, 365, 730],
        index=2,
        format_func=lambda days: f"Last {days} days",
    )

    st.subheader("Potentially underutilized candidates")
    st.caption(
        "Candidate signal: proficiency ≥ 4, last used before the selected lookback "
        "(or no last-used date), and no assignment active/recent in that window. "
        "It does not measure workload or availability."
    )
    with st.expander("Underutilized-candidate calculation"):
        st.markdown(
            """
            `recent_assignments` is a CTE of people whose assignment end date is within
            the window (open assignments are treated as active). `strongest_stale_skills`
            picks each person's highest-proficiency skill that meets the recency rule.
            A `LEFT JOIN` followed by `WHERE recent.person_id IS NULL` keeps people who
            have no qualifying assignment. The proficiency threshold is fixed at 4/5;
            the date window is selected above. This is a heuristic for review, not proof
            that someone is underused.
            """
        )
        st.code(
            """WITH recent_assignments AS (...),
strongest_stale_skills AS (...)
SELECT person_and_skill_details
FROM strongest_stale_skills
LEFT JOIN recent_assignments USING (person_id)
WHERE recent_assignments.person_id IS NULL;""",
            language="sql",
        )
    underused = _read_frame(
        """
        -- Find people with a stale high-proficiency skill and no recent assignment.
        WITH recent_assignments AS (
            SELECT DISTINCT person_id
            FROM capstone.assignment
            WHERE COALESCE(to_date, CURRENT_DATE) >= CURRENT_DATE - (%s * INTERVAL '1 day')
              AND (from_date IS NULL OR from_date <= CURRENT_DATE)
        ),
        strongest_stale_skills AS (
            SELECT DISTINCT ON (ps.person_id)
                   ps.person_id, s.name AS skill, ps.proficiency,
                   ps.last_used_date
            FROM capstone.person_skill ps
            JOIN capstone.skill s ON s.skill_id = ps.skill_id
            WHERE ps.proficiency >= 4
              AND (ps.last_used_date IS NULL OR
                   ps.last_used_date < CURRENT_DATE - (%s * INTERVAL '1 day'))
            ORDER BY ps.person_id, ps.proficiency DESC,
                     ps.last_used_date NULLS FIRST, s.name
        )
        SELECT p.person_id, p.name, p.department, p.role,
               stale.skill AS strong_stale_skill, stale.proficiency,
               stale.last_used_date
        FROM strongest_stale_skills stale
        JOIN capstone.person p ON p.person_id = stale.person_id
        LEFT JOIN recent_assignments recent ON recent.person_id = p.person_id
        WHERE recent.person_id IS NULL
        ORDER BY stale.proficiency DESC, stale.last_used_date NULLS FIRST, p.name
        """,
        (window, window),
    )
    if underused.empty:
        st.info("No candidates meet both selected signals in this period.")
    else:
        st.dataframe(
            underused.drop(columns=["person_id"]),
            hide_index=True,
            width="stretch",
        )

    st.subheader("Top collaborators")
    with st.expander("Top-collaborator calculation"):
        st.markdown(
            """
            `participants` uses `UNION ALL` to produce one row for each endpoint of
            every interaction dated inside the selected window. `collaborator_totals`
            sums the database's `frequency` value and counts interaction records. A
            person appearing on both ends receives credit as a participant on each
            interaction row; frequency is a recorded count, not a message or meeting
            count independently verified by this dashboard.
            """
        )
        st.code(
            """WITH participants AS (
    SELECT person_a AS person_id, frequency FROM interaction
    UNION ALL
    SELECT person_b AS person_id, frequency FROM interaction
),
collaborator_totals AS (
    SELECT person_id, SUM(frequency) FROM participants GROUP BY person_id
)
SELECT people_and_totals FROM collaborator_totals;""",
            language="sql",
        )
    collaborators = _read_frame(
        """
        -- Expand each interaction to both participants, then aggregate recent activity.
        WITH participants AS (
            SELECT person_a AS person_id, frequency, last_contact
            FROM capstone.interaction
            WHERE last_contact >= CURRENT_DATE - (%s * INTERVAL '1 day')
            UNION ALL
            SELECT person_b AS person_id, frequency, last_contact
            FROM capstone.interaction
            WHERE last_contact >= CURRENT_DATE - (%s * INTERVAL '1 day')
        ),
        collaborator_totals AS (
            SELECT person_id, SUM(frequency) AS total_interactions,
                   COUNT(*) AS interaction_records,
                   MAX(last_contact) AS latest_contact
            FROM participants
            GROUP BY person_id
        )
        SELECT p.person_id, p.name, totals.total_interactions,
               totals.interaction_records, totals.latest_contact
        FROM collaborator_totals totals
        JOIN capstone.person p ON p.person_id = totals.person_id
        ORDER BY totals.total_interactions DESC, totals.interaction_records DESC, p.name
        LIMIT 15
        """,
        (window, window),
    )
    if collaborators.empty:
        st.info("No collaboration records fall within the selected period.")
    else:
        st.bar_chart(
            collaborators.set_index("name")[["total_interactions"]]
        )
        st.dataframe(
            collaborators.drop(columns=["person_id"]),
            hide_index=True,
            width="stretch",
        )

    st.subheader("Project-wise required-skill coverage")
    with st.expander("Project coverage calculation"):
        st.markdown(
            """
            `required_skills` selects rows marked `Required` in `project_skill`.
            `project_coverage` counts a requirement as covered if an assigned person's
            `person_skill` row has the same skill ID. Coverage is covered requirements
            divided by required requirements. Projects with no required skills are
            shown as “No requirements,” not as 0% or 100%. No skill proficiency cutoff
            is applied.
            """
        )
        st.code(
            """WITH required_skills AS (...),
project_coverage AS (
    SELECT project_id,
           COUNT(required_skill) AS total_required,
           COUNT(required_skill) FILTER (WHERE assigned_team_has_skill)
               AS covered_required
    FROM required_skills
    GROUP BY project_id
)
SELECT coverage_percent FROM project_coverage;""",
            language="sql",
        )
    coverage = _read_frame(
        """
        -- Compare required project skills with skills held by assigned team members.
        WITH required_skills AS (
            SELECT ps.project_id, ps.skill_id, s.name AS skill
            FROM capstone.project_skill ps
            JOIN capstone.skill s ON s.skill_id = ps.skill_id
            WHERE ps.importance ILIKE 'required'
        ),
        project_coverage AS (
            SELECT r.project_id,
                   COUNT(DISTINCT r.skill_id) AS total_required,
                   COUNT(DISTINCT r.skill_id) FILTER (
                       WHERE EXISTS (
                           SELECT 1
                           FROM capstone.assignment a
                           JOIN capstone.person_skill held
                             ON held.person_id = a.person_id
                           WHERE a.project_id = r.project_id
                             AND held.skill_id = r.skill_id
                       )
                   ) AS covered_required,
                   string_agg(DISTINCT r.skill, ', ' ORDER BY r.skill)
                       AS required_skills,
                   string_agg(DISTINCT r.skill, ', ' ORDER BY r.skill) FILTER (
                       WHERE NOT EXISTS (
                           SELECT 1
                           FROM capstone.assignment a
                           JOIN capstone.person_skill held
                             ON held.person_id = a.person_id
                           WHERE a.project_id = r.project_id
                             AND held.skill_id = r.skill_id
                       )
                   ) AS uncovered_skills
            FROM required_skills r
            GROUP BY r.project_id
        )
        SELECT proj.project_id, proj.title, proj.domain,
               COALESCE(c.covered_required, 0) AS covered_required,
               COALESCE(c.total_required, 0) AS total_required,
               CASE
                   WHEN COALESCE(c.total_required, 0) = 0 THEN NULL
                   ELSE ROUND(
                       100.0 * c.covered_required / c.total_required, 1
                   )
               END AS coverage_percent,
               c.required_skills, c.uncovered_skills
        FROM capstone.project proj
        LEFT JOIN project_coverage c ON c.project_id = proj.project_id
        ORDER BY coverage_percent NULLS LAST, proj.title
        """
    )
    coverage["coverage_percent"] = pd.to_numeric(
        coverage["coverage_percent"], errors="coerce"
    )
    if coverage.empty:
        st.info("No project data found.")
    else:
        st.bar_chart(
            coverage.dropna(subset=["coverage_percent"])
            .set_index("title")[["coverage_percent"]]
        )
        st.dataframe(
            coverage.drop(columns=["project_id"]),
            hide_index=True,
            width="stretch",
        )


def main():
    st.set_page_config(
        page_title="KMS Data Dashboard",
        page_icon="📊",
        layout="wide",
    )
    st.title("Knowledge Management System Dashboard")
    st.caption(
        "Explore and maintain the normalized PostgreSQL data behind the KMS. "
        "Changes are written directly to the configured database."
    )
    if not DATABASE_URL:
        st.error("DATABASE_URL is missing. Add it to your local .env file.")
        st.stop()

    try:
        pages = [
            "Overview",
            "People",
            "Projects",
            "Insights",
            "Data management",
        ]
        page = st.sidebar.radio("Dashboard page", pages)
        if page == "Overview":
            st.header("Organization overview")
            _show_overview()
        elif page == "People":
            _show_people_dashboard()
        elif page == "Projects":
            _show_projects_dashboard()
        elif page == "Insights":
            _show_insights()
        else:
            st.header("Data management")
            st.caption(
                "Direct maintenance for normalized tables. Browse views show names "
                "and labels; database IDs are kept in the editor only for relationships."
            )
            table_page = st.selectbox(
                "Choose a data area",
                list(TABLES),
                key="admin_table_selector",
            )
            config = TABLES[table_page]
            st.subheader(table_page)
            st.caption(
                f"Table: capstone.{config['table']} · Primary key: "
                + "stored internally for record selection"
            )
            search_text = st.text_input(
                "Search records",
                placeholder="Search names, titles, skills, roles, or collaboration channels",
                key=f"search_{config['table']}",
            )
            date_range = None
            if config["date"]:
                use_date_filter = st.checkbox(
                    f"Filter by {config['date'].replace('_', ' ')} range",
                    key=f"enable_date_{config['table']}",
                )
                if use_date_filter:
                    first, second = st.columns(2)
                    start_date = first.date_input(
                        "From",
                        value=date(date.today().year - 20, 1, 1),
                        key=f"date_from_{config['table']}",
                    )
                    end_date = second.date_input(
                        "To",
                        value=date.today(),
                        key=f"date_to_{config['table']}",
                    )
                    if start_date > end_date:
                        st.error("The start date must be on or before the end date.")
                        st.stop()
                    date_range = (start_date, end_date)

            frame = _table_frame(config, search_text, date_range)
            browse_frame = _browse_frame(config, search_text, date_range)
            st.caption(f"{len(frame)} matching record(s)")
            st.dataframe(browse_frame, hide_index=True, width="stretch")
            _manage_table(table_page, config, frame)
    except psycopg2.Error as error:
        st.error(f"Database operation failed: {error}")
    except (ValueError, RuntimeError) as error:
        st.error(f"Dashboard could not complete the requested operation: {error}")


if __name__ == "__main__":
    main()
