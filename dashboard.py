import os
import html
from contextlib import closing
from datetime import datetime

import altair as alt
import numpy as np

from rag_backend import embedding_graph_data

import pandas as pd
import psycopg2
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL")

st.set_page_config(
    page_title="Organisation Intelligence System",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# THEME
# ============================================================

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

if st.session_state.dark_mode:
    BG = "#171719"
    CARD = "#222225"
    TEXT = "#F4F1EF"
    MUTED = "#B8B0B0"
    PRIMARY = "#A83D52"
    PRIMARY_DARK = "#7F2B3D"
    BORDER = "#383438"
    SIDEBAR = "#1D1B1D"
    SOFT = "#2A2527"
else:
    BG = "#F7F4F1"
    CARD = "#FFFFFF"
    TEXT = "#242124"
    MUTED = "#6F6868"
    PRIMARY = "#6B1E2E"
    PRIMARY_DARK = "#531622"
    BORDER = "#E4DCDD"
    SIDEBAR = "#F0EBE8"
    SOFT = "#F2E8EA"


# ============================================================
# GLOBAL CSS
# ============================================================

st.markdown(
    f"""
    <style>

    .stApp {{
        background: {BG};
        color: {TEXT};
    }}

    [data-testid="stSidebar"] {{
        background: {SIDEBAR};
        border-right: 1px solid {BORDER};
    }}

    [data-testid="stSidebar"] * {{
        color: {TEXT};
    }}

    h1, h2, h3, h4 {{
        color: {TEXT} !important;
        letter-spacing: -0.02em;
    }}

    p, label, span {{
        color: {TEXT};
    }}

    .block-container {{
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }}

    /* --------------------------------------------------------
       HERO
       -------------------------------------------------------- */

    .hero {{
        background: linear-gradient(
            135deg,
            {PRIMARY} 0%,
            {PRIMARY_DARK} 100%
        );
        border-radius: 18px;
        padding: 30px 34px;
        margin-bottom: 26px;
        box-shadow: 0 10px 30px rgba(70, 20, 30, 0.15);
    }}

    .hero h1,
    .hero h2,
    .hero h3,
    .hero h4,
    .hero p,
    .hero span,
    .hero div {{
        color: #FFFFFF !important;
    }}

    /* --------------------------------------------------------
       BURGUNDY BOX TEXT
       -------------------------------------------------------- */

    .burgundy-box,
    .burgundy-box * {{
        color: #FFFFFF !important;
    }}

    .burgundy-box h1,
    .burgundy-box h2,
    .burgundy-box h3,
    .burgundy-box h4,
    .burgundy-box p,
    .burgundy-box span,
    .burgundy-box label {{
        color: #FFFFFF !important;
    }}

    /* --------------------------------------------------------
       SECTION HEADERS
       -------------------------------------------------------- */

    .section-title {{
        font-size: 1.25rem;
        font-weight: 700;
        color: {TEXT};
        margin-top: 24px;
        margin-bottom: 12px;
    }}

    .section-subtitle {{
        color: {MUTED};
        font-size: 0.9rem;
        margin-bottom: 16px;
    }}

    /* --------------------------------------------------------
       METRICS
       -------------------------------------------------------- */

    .metric-card {{
        background: {CARD};
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 20px;
        min-height: 115px;
        box-shadow: 0 4px 14px rgba(30, 20, 20, 0.04);
    }}

    .metric-label {{
        color: {MUTED};
        font-size: 0.82rem;
        margin-bottom: 8px;
    }}

    .metric-value {{
        color: {PRIMARY};
        font-size: 1.8rem;
        font-weight: 750;
    }}

    /* --------------------------------------------------------
       INSIGHT CARDS
       -------------------------------------------------------- */

    .insight-card {{
        background: {CARD};
        border: 1px solid {BORDER};
        border-left: 4px solid {PRIMARY};
        border-radius: 12px;
        padding: 15px 17px;
        margin-bottom: 10px;
    }}

    .insight-title {{
        font-weight: 700;
        margin-bottom: 5px;
        color: {TEXT};
    }}

    .insight-text {{
        color: {MUTED};
        font-size: 0.9rem;
    }}

    /* --------------------------------------------------------
       ANSWER BOX
       -------------------------------------------------------- */

    .answer-box {{
        background: {SOFT};
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 20px;
        margin: 12px 0 20px 0;
        color: {TEXT} !important;
    }}

    .answer-box p,
    .answer-box span,
    .answer-box div,
    .answer-box li {{
        color: {TEXT} !important;
    }}

    .answer-title {{
        color: {PRIMARY} !important;
        font-weight: 700;
        margin-bottom: 8px;
    }}

    /* --------------------------------------------------------
       SIDEBAR BRAND
       -------------------------------------------------------- */

    .brand {{
        padding: 8px 4px 22px 4px;
    }}

    .brand-title {{
        color: {PRIMARY};
        font-size: 1.15rem;
        font-weight: 800;
        letter-spacing: 0.04em;
    }}

    .brand-subtitle {{
        color: {MUTED};
        font-size: 0.75rem;
        margin-top: 4px;
    }}

    /* --------------------------------------------------------
       REPORT PREVIEW
       -------------------------------------------------------- */

    .report-card {{
        background: {CARD};
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 12px;
    }}

    /* --------------------------------------------------------
       STREAMLIT ELEMENTS
       -------------------------------------------------------- */

    .stButton > button {{
        border-radius: 9px;
        border: 1px solid {PRIMARY};
        background: {PRIMARY};
        color: #FFFFFF !important;
        font-weight: 600;
    }}

    .stButton > button:hover {{
        background: {PRIMARY_DARK};
        border-color: {PRIMARY_DARK};
        color: #FFFFFF !important;
    }}

    .stButton > button p {{
        color: #FFFFFF !important;
    }}

    .stButton > button span {{
        color: #FFFFFF !important;
    }}

    /* --------------------------------------------------------
       LIGHT SECONDARY / NATIVE BUTTONS
       -------------------------------------------------------- */

    button[kind="secondary"] {{
        color: #242124 !important;
    }}

    button[kind="secondary"] p,
    button[kind="secondary"] span {{
        color: #242124 !important;
    }}

    /* --------------------------------------------------------
       DOWNLOAD BUTTONS
       -------------------------------------------------------- */

    .stDownloadButton > button {{
        border-radius: 9px;
        color: #242124 !important;
    }}

    .stDownloadButton > button p,
    .stDownloadButton > button span {{
        color: #242124 !important;
    }}

    /* --------------------------------------------------------
    CHART / TABLE TOOLBAR
    -------------------------------------------------------- */

    [data-testid="stElementToolbar"] button {{
        color: #242124 !important;
    }}

    [data-testid="stElementToolbar"] button svg {{
        color: #242124 !important;
        fill: #242124 !important;
    }}

    [data-testid="stElementToolbar"] button:hover {{
        color: {PRIMARY} !important;
    }}

    [data-testid="stElementToolbar"] button:hover svg {{
        color: {PRIMARY} !important;
        fill: {PRIMARY} !important;
    }}

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DATABASE
# ============================================================

if not DATABASE_URL:
    st.error(
        "DATABASE_URL was not found. Please check the .env file in the project folder."
    )
    st.stop()


@st.cache_data(ttl=60)
def read_sql(query, params=None):
    with closing(psycopg2.connect(DATABASE_URL)) as connection:
        return pd.read_sql_query(query, connection, params=params)


# ============================================================
# DATA LOADERS
# ============================================================

@st.cache_data(ttl=60)
def load_people():
    return read_sql(
        """
        SELECT
            person_id,
            name,
            department,
            role,
            joined_date
        FROM capstone.person
        ORDER BY name
        """
    )


@st.cache_data(ttl=60)
def load_skills():
    return read_sql(
        """
        SELECT
            skill_id,
            name AS skill,
            category
        FROM capstone.skill
        ORDER BY name
        """
    )


@st.cache_data(ttl=60)
def load_projects():
    return read_sql(
        """
        SELECT
            project_id,
            title AS project,
            domain,
            client_type,
            outcome,
            start_date,
            end_date
        FROM capstone.project
        ORDER BY start_date DESC, title
        """
    )


@st.cache_data(ttl=60)
def load_person_skills():
    return read_sql(
        """
        SELECT
            ps.person_id,
            p.name AS person,
            ps.skill_id,
            s.name AS skill,
            s.category,
            ps.proficiency,
            ps.last_used_date
        FROM capstone.person_skill ps
        JOIN capstone.person p
            ON p.person_id = ps.person_id
        JOIN capstone.skill s
            ON s.skill_id = ps.skill_id
        ORDER BY p.name, s.name
        """
    )


@st.cache_data(ttl=60)
def load_assignments():
    return read_sql(
        """
        SELECT
            a.assignment_id,
            a.person_id,
            p.name AS person,
            a.project_id,
            pr.title AS project,
            a.from_date,
            a.to_date
        FROM capstone.assignment a
        JOIN capstone.person p
            ON p.person_id = a.person_id
        JOIN capstone.project pr
            ON pr.project_id = a.project_id
        ORDER BY pr.title, p.name
        """
    )


@st.cache_data(ttl=60)
def load_project_skills():
    return read_sql(
        """
        SELECT
            ps.project_id,
            pr.title AS project,
            ps.skill_id,
            s.name AS skill,
            s.category,
            ps.importance
        FROM capstone.project_skill ps
        JOIN capstone.project pr
            ON pr.project_id = ps.project_id
        JOIN capstone.skill s
            ON s.skill_id = ps.skill_id
        ORDER BY pr.title, ps.importance DESC, s.name
        """
    )


@st.cache_data(ttl=60)
def load_interactions():
    return read_sql(
        """
        SELECT
            i.interaction_id,
            i.person_a,
            pa.name AS person_a_name,
            i.person_b,
            pb.name AS person_b_name,
            i.project_id,
            pr.title AS project,
            i.channel,
            i.frequency,
            i.last_contact
        FROM capstone.interaction i
        JOIN capstone.person pa
            ON pa.person_id = i.person_a
        JOIN capstone.person pb
            ON pb.person_id = i.person_b
        LEFT JOIN capstone.project pr
            ON pr.project_id = i.project_id
        ORDER BY i.frequency DESC
        """
    )


# ============================================================
# GENERIC HELPERS
# ============================================================

def metric_card(label, value):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{html.escape(str(label))}</div>
            <div class="metric-value">{html.escape(str(value))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title, subtitle=None):
    st.markdown(
        f'<div class="section-title">{html.escape(title)}</div>',
        unsafe_allow_html=True,
    )

    if subtitle:
        st.markdown(
            f'<div class="section-subtitle">{html.escape(subtitle)}</div>',
            unsafe_allow_html=True,
        )


def hero(title, subtitle):
    st.markdown(
        f"""
        <div class="hero">
            <h1>{html.escape(title)}</h1>
            <p>{html.escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def clean_text(value):
    return str(value).strip().lower()


def filter_dataframe(
    df,
    key_prefix,
    search_columns=None,
    filter_columns=None,
    show_column_selector=True,
):
    """
    Reusable table control:

    - Search
    - Categorical filters
    - Visible-column selector
    - Native Streamlit dataframe sorting
    - CSV download
    """

    if df.empty:
        st.info("No records available.")
        return df

    working = df.copy()

    search_columns = search_columns or []
    filter_columns = filter_columns or []

    # -------------------------
    # Search
    # -------------------------

    if search_columns:
        search = st.text_input(
            "Search",
            placeholder="Search this table...",
            key=f"{key_prefix}_search",
        )

        if search:
            search = clean_text(search)

            mask = pd.Series(False, index=working.index)

            for column in search_columns:
                if column in working.columns:
                    mask = mask | working[column].astype(str).str.lower().str.contains(
                        search,
                        na=False,
                    )

            working = working[mask]

    # -------------------------
    # Filters
    # -------------------------

    if filter_columns:
        cols = st.columns(min(len(filter_columns), 3))

        for idx, column in enumerate(filter_columns):
            if column not in working.columns:
                continue

            values = (
                working[column]
                .dropna()
                .astype(str)
                .sort_values()
                .unique()
                .tolist()
            )

            if not values:
                continue

            with cols[idx % len(cols)]:
                selected = st.multiselect(
                    f"{column}",
                    values,
                    key=f"{key_prefix}_{column}",
                )

                if selected:
                    working = working[
                        working[column].astype(str).isin(selected)
                    ]

    # -------------------------
    # Visible columns
    # -------------------------

    if show_column_selector:
        all_columns = list(working.columns)

        selected_columns = st.multiselect(
            "Columns to display",
            all_columns,
            default=all_columns,
            key=f"{key_prefix}_columns",
        )

        if selected_columns:
            display_df = working[selected_columns]
        else:
            display_df = working
    else:
        display_df = working

    # -------------------------
    # Summary
    # -------------------------

    st.caption(
        f"Showing {len(display_df):,} of {len(df):,} records"
    )

    # -------------------------
    # Table
    # -------------------------

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )

    # -------------------------
    # Download
    # -------------------------

    csv = display_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download CSV",
        csv,
        file_name=f"{key_prefix}.csv",
        mime="text/csv",
        key=f"{key_prefix}_download",
    )

    return working


def safe_date(value):
    if pd.isna(value):
        return "—"

    try:
        return pd.to_datetime(value).strftime("%d %b %Y")
    except Exception:
        return str(value)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="brand">
            <div class="brand-title">◈ ORGANISATION INTELLIGENCE</div>
            <div class="brand-subtitle">
                Knowledge Management System
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    page = st.radio(
        "Navigate",
        [
            "Executive Overview",
            "People Intelligence",
            "Project Intelligence",
            "Skills Intelligence",
            "Organisation Network",
            "Ask Intelligence",
            "Report Centre",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    new_dark_mode = st.toggle(
        "Dark mode",
        value=st.session_state.dark_mode,
    )

    if new_dark_mode != st.session_state.dark_mode:
        st.session_state.dark_mode = new_dark_mode
        st.rerun()

    st.caption("BDM Capstone • Organisation Intelligence System")


# ============================================================
# EXECUTIVE OVERVIEW
# ============================================================

def show_overview():

    people = load_people()
    skills = load_skills()
    projects = load_projects()
    assignments = load_assignments()
    person_skills = load_person_skills()

    hero(
        "Organisation Intelligence System",
        "A central view of workforce capabilities, projects, skills and organisational knowledge.",
    )

    # -------------------------
    # KPIs
    # -------------------------

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card("People", len(people))

    with c2:
        metric_card("Skills", len(skills))

    with c3:
        metric_card("Projects", len(projects))

    with c4:
        metric_card("Assignments", len(assignments))

    # -------------------------
    # Workforce snapshot
    # -------------------------

    section_header(
        "Workforce Snapshot",
        "Understand how organisational talent is distributed.",
    )

    col1, col2 = st.columns(2)

    with col1:
        dept_counts = (
            people["department"]
            .value_counts()
            .rename_axis("Department")
            .reset_index(name="People")
        )

        st.bar_chart(
            dept_counts.set_index("Department"),
            height=300,
        )

    with col2:
        role_counts = (
            people["role"]
            .value_counts()
            .rename_axis("Role")
            .reset_index(name="People")
        )

        st.bar_chart(
            role_counts.set_index("Role"),
            height=300,
        )

    # -------------------------
    # Skill snapshot
    # -------------------------

    section_header(
        "Capability Snapshot",
        "Skills represented across the organisation.",
    )

    skill_counts = (
        person_skills.groupby("skill")
        .size()
        .sort_values(ascending=False)
        .head(10)
    )

    st.bar_chart(
        skill_counts,
        height=320,
    )

    # -------------------------
    # Portfolio
    # -------------------------

    section_header(
        "Project Portfolio",
        "Current projects and their basic business context.",
    )

    portfolio = projects[
        [
            "project_id",
            "project",
            "domain",
            "client_type",
            "outcome",
            "start_date",
            "end_date",
        ]
    ].copy()

    filter_dataframe(
        portfolio,
        "overview_projects",
        search_columns=[
            "project",
            "domain",
            "client_type",
            "outcome",
        ],
        filter_columns=[
            "domain",
            "client_type",
            "outcome",
        ],
    )


# ============================================================
# PEOPLE INTELLIGENCE
# ============================================================

def show_people():

    people = load_people()
    person_skills = load_person_skills()
    assignments = load_assignments()
    interactions = load_interactions()

    hero(
        "People Intelligence",
        "Explore employees, capabilities, project experience and collaboration relationships.",
    )

    # -------------------------
    # Search / filtering
    # -------------------------

    section_header(
        "Employee Directory",
        "Search by name, department or role and narrow the employee list.",
    )

    filtered_people = people.copy()

    col1, col2 = st.columns([2, 1])

    with col1:
        search = st.text_input(
            "Search employees",
            placeholder="e.g. Ben Carter, Engineering, ML Engineer",
            key="people_search",
        )

    with col2:
        departments = ["All departments"] + sorted(
            people["department"].dropna().astype(str).unique().tolist()
        )

        department = st.selectbox(
            "Department",
            departments,
            key="people_department",
        )

    if search:
        search_value = clean_text(search)

        mask = (
            people["name"].astype(str).str.lower().str.contains(
                search_value,
                na=False,
            )
            |
            people["department"].astype(str).str.lower().str.contains(
                search_value,
                na=False,
            )
            |
            people["role"].astype(str).str.lower().str.contains(
                search_value,
                na=False,
            )
        )

        filtered_people = people[mask]

    if department != "All departments":
        filtered_people = filtered_people[
            filtered_people["department"] == department
        ]

    # -------------------------
    # KPIs
    # -------------------------

    c1, c2, c3 = st.columns(3)

    with c1:
        metric_card("Matching People", len(filtered_people))

    with c2:
        metric_card(
            "Departments",
            filtered_people["department"].nunique(),
        )

    with c3:
        metric_card(
            "Roles",
            filtered_people["role"].nunique(),
        )

    # -------------------------
    # Directory
    # -------------------------

    directory = filtered_people.copy()

    filter_dataframe(
        directory,
        "people_directory",
        search_columns=["name", "department", "role"],
        filter_columns=["department", "role"],
    )

    # -------------------------
    # Employee selector
    # -------------------------

    section_header(
        "Employee Profile",
        "Select any employee from the filtered list to inspect their organisational profile.",
    )

    if filtered_people.empty:
        st.warning("No employees match the selected search/filter criteria.")
        return

    employee_options = (
        filtered_people
        .sort_values("name")["name"]
        .tolist()
    )

    selected_employee = st.selectbox(
        "Select employee",
        employee_options,
        key="employee_profile_selector",
    )

    person_row = filtered_people[
        filtered_people["name"] == selected_employee
    ].iloc[0]

    person_id = person_row["person_id"]

    # -------------------------
    # Profile header
    # -------------------------

    st.markdown(
        f"""
        <div class="answer-box">
            <div class="answer-title">
                {html.escape(selected_employee)}
            </div>
            <div>
                {html.escape(str(person_row["role"]))}
                ·
                {html.escape(str(person_row["department"]))}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        metric_card("Department", person_row["department"])

    with c2:
        metric_card("Role", person_row["role"])

    with c3:
        metric_card(
            "Joined",
            safe_date(person_row["joined_date"]),
        )

    # -------------------------
    # Capabilities
    # -------------------------

    section_header("Capability Profile")

    employee_skills = person_skills[
        person_skills["person_id"] == person_id
    ].copy()

    if employee_skills.empty:
        st.info("No skills recorded for this employee.")
    else:
        employee_skills = employee_skills[
            [
                "skill",
                "category",
                "proficiency",
                
            ]
        ].sort_values(
            ["proficiency"],
            ascending=False,
        )

        filter_dataframe(
            employee_skills,
            f"profile_skills_{person_id}",
            search_columns=["skill", "category"],
            filter_columns=["category"],
        )

    # -------------------------
    # Project history
    # -------------------------

    section_header("Project History")

    employee_projects = assignments[
        assignments["person_id"] == person_id
    ][
        [
            "project_id",
            "project",
        ]
    ].drop_duplicates()

    if employee_projects.empty:
        st.info("No project assignments recorded.")
    else:
        filter_dataframe(
            employee_projects,
            f"profile_projects_{person_id}",
            search_columns=["project"],
        )

    # -------------------------
    # Collaboration
    # -------------------------

    section_header("Collaboration")

    employee_interactions = interactions[
        (interactions["person_a"] == person_id)
        |
        (interactions["person_b"] == person_id)
    ].copy()

    if employee_interactions.empty:
        st.info("No collaboration relationships recorded.")
    else:

        employee_interactions["colleague"] = employee_interactions.apply(
            lambda row:
                row["person_b_name"]
                if row["person_a"] == person_id
                else row["person_a_name"],
            axis=1,
        )

        collaboration = employee_interactions[
            [
                "colleague",
                "project",
            ]
        ].drop_duplicates()

        filter_dataframe(
            collaboration,
            f"profile_collaboration_{person_id}",
            search_columns=["colleague", "project"],
            filter_columns=["project"],
        )

# ============================================================
# PROJECT INTELLIGENCE
# ============================================================

def show_projects():

    projects = load_projects()
    assignments = load_assignments()
    project_skills = load_project_skills()
    person_skills = load_person_skills()
    people = load_people()

    hero(
        "Project Intelligence",
        "Understand project teams, required capabilities and current capability coverage.",
    )

    if projects.empty:
        st.info("No projects available.")
        return

    # -------------------------
    # Project selector
    # -------------------------

    project_names = (
        projects
        .sort_values("project")
        ["project"]
        .tolist()
    )

    selected_project = st.selectbox(
        "Select project",
        project_names,
        key="project_selector",
    )

    project = projects[
        projects["project"] == selected_project
    ].iloc[0]

    project_id = project["project_id"]

    # -------------------------
    # Project KPIs
    # -------------------------

    team = assignments[
        assignments["project_id"] == project_id
    ].copy()

    requirements = project_skills[
        project_skills["project_id"] == project_id
    ].copy()

    team_size = len(team)
    required_count = len(requirements)

    # Exact skill coverage
    team_person_ids = team["person_id"].tolist()

    team_skill_data = person_skills[
        person_skills["person_id"].isin(team_person_ids)
    ].copy()

    covered_skills = set(
        team_skill_data["skill"].astype(str).str.lower()
    )

    required_skills = set(
        requirements["skill"].astype(str).str.lower()
    )

    covered_count = len(
        covered_skills.intersection(required_skills)
    )

    coverage_pct = (
        round((covered_count / required_count) * 100)
        if required_count
        else 100
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card("Team Size", team_size)

    with c2:
        metric_card("Skills Required", required_count)

    with c3:
        metric_card("Skill Coverage", f"{coverage_pct}%")

    with c4:
        metric_card("Domain", project["domain"])

    # -------------------------
    # Project profile
    # -------------------------

    section_header("Project Profile")

    profile = pd.DataFrame(
        {
            "Field": [
                "Project",
                "Domain",
                "Client Type",
                "Outcome",
                "Start Date",
                "End Date",
            ],
            "Value": [
                project["project"],
                project["domain"],
                project["client_type"],
                project["outcome"],
                safe_date(project["start_date"]),
                safe_date(project["end_date"]),
            ],
        }
    )

    st.dataframe(
        profile,
        use_container_width=True,
        hide_index=True,
    )

    # -------------------------
    # Team
    # -------------------------

    section_header(
        "Project Team",
        "Employees currently assigned to this project.",
    )

    if team.empty:
        st.info("No team members are recorded.")
    else:
        team_display = team.merge(
            people[
                [
                    "person_id",
                    "department",
                    "role",
                ]
            ],
            on="person_id",
            how="left",
        )

        team_display = team_display[
            [
                "person",
                "department",
                "role",
            ]
        ]

        filter_dataframe(
            team_display,
            f"project_team_{project_id}",
            search_columns=["person", "department", "role"],
            filter_columns=["department", "role"],
        )

    # -------------------------
    # Required skills
    # -------------------------

    section_header(
        "Required Capabilities",
        "Skills explicitly associated with this project.",
    )

    if requirements.empty:
        st.info("No project skill requirements recorded.")
    else:

        requirement_display = requirements[
            [
                "skill",
                "category",
                "importance",
            ]
        ].copy()

        filter_dataframe(
            requirement_display,
            f"project_requirements_{project_id}",
            search_columns=["skill", "category"],
            filter_columns=["category", "importance"],
        )

    # -------------------------
    # Capability coverage
    # -------------------------

    section_header(
        "Capability Coverage",
        "Compares project requirements with the capabilities available in the assigned team.",
    )

    coverage_rows = []

    for _, req in requirements.iterrows():

        skill_name = req["skill"]

        matching = team_skill_data[
            team_skill_data["skill"].str.lower()
            == str(skill_name).lower()
        ]

        if matching.empty:
            coverage = "Gap"
            best_proficiency = 0
        else:
            coverage = "Covered"
            best_proficiency = matching["proficiency"].max()

        coverage_rows.append(
            {
                "Skill": skill_name,
                "Importance": req["importance"],
                "Coverage": coverage,
                "Best Team Proficiency": best_proficiency,
            }
        )

    coverage_df = pd.DataFrame(coverage_rows)

    if coverage_df.empty:
        st.info("No capability coverage data available.")
    else:

        filter_dataframe(
            coverage_df,
            f"project_coverage_{project_id}",
            search_columns=["Skill", "Coverage"],
            filter_columns=["Coverage", "Importance"],
        )

        gaps = coverage_df[
            coverage_df["Coverage"] == "Gap"
        ]

        if not gaps.empty:
            st.warning(
                f"{len(gaps)} required capability/capabilities are not represented "
                "in the current project team."
            )
        else:
            st.success(
                "All recorded required capabilities are represented in the current team."
            )

    # -------------------------
    # Internal staffing matches
    # -------------------------

    section_header(
        "Internal Capability Matches",
        "Employees outside the current project team who possess required project skills.",
    )

    if requirements.empty:
        st.info("No requirements available for matching.")
        return

    current_team_ids = set(team["person_id"].tolist())

    required_skill_names = set(
        requirements["skill"].astype(str).str.lower()
    )

    candidate_skills = person_skills[
        person_skills["skill"].astype(str).str.lower().isin(
            required_skill_names
        )
        &
        ~person_skills["person_id"].isin(current_team_ids)
    ].copy()

    if candidate_skills.empty:
        st.info(
            "No additional internal employees were found with the recorded required skills."
        )
    else:

        candidate_summary = (
            candidate_skills
            .groupby(
                [
                    "person_id",
                    "person",
                ]
            )
            .agg(
                Matching_Skills=("skill", "nunique"),
                Matched_Skill_Names=(
                    "skill",
                    lambda x: ", ".join(
                        sorted(
                            {
                                str(skill)
                                for skill in x
                            }
                        )
                    ),
                ),
                Average_Proficiency=("proficiency", "mean"),
            )
            .reset_index()
        )

        candidate_summary["Average_Proficiency"] = (
            candidate_summary["Average_Proficiency"]
            .round(2)
        )

        candidate_summary = candidate_summary.sort_values(
            [
                "Matching_Skills",
                "Average_Proficiency",
            ],
            ascending=False,
        )

        candidate_summary = candidate_summary.rename(
            columns={
                "Matching_Skills": "Matching Skills",
                "Matched_Skill_Names": "Matched Skill Names",
                "Average_Proficiency": "Proficiency",
            }
        )

        filter_dataframe(
            candidate_summary,
            f"project_candidates_{project_id}",
            search_columns=[
                "person",
                "Matched Skill Names",
            ],
        )

        st.caption(
            "This is a capability-matching signal based on recorded skills and proficiency; "
            "it is not a trained prediction model."
        )


# ============================================================
# SKILLS INTELLIGENCE
# ============================================================

def show_skills():

    skills = load_skills()
    person_skills = load_person_skills()
    project_skills = load_project_skills()

    hero(
        "Skills Intelligence",
        "Understand the organisation's capability inventory, proficiency and project demand.",
    )

    # -------------------------
    # KPIs
    # -------------------------

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card("Total Skills", len(skills))

    with c2:
        metric_card(
            "Technical Skills",
            len(
                skills[
                    skills["category"].str.lower() == "technical"
                ]
            ),
        )

    with c3:
        metric_card(
            "Skill Records",
            len(person_skills),
        )

    with c4:
        metric_card(
            "Project Requirements",
            len(project_skills),
        )

    # -------------------------
    # Skill inventory
    # -------------------------

    section_header(
        "Skill Inventory",
        "Search and filter the complete organisational skill catalogue.",
    )

    filter_dataframe(
        skills,
        "skill_inventory",
        search_columns=["skill", "category"],
        filter_columns=["category"],
    )

    # -------------------------
    # Skill adoption
    # -------------------------

    section_header(
        "Skill Adoption & Proficiency",
        "Shows how widely each skill is represented and the recorded proficiency level.",
    )

    adoption = (
        person_skills
        .groupby("skill")
        .agg(
            People=("person_id", "nunique"),
            Average_Proficiency=("proficiency", "mean"),
            
        )
        .reset_index()
    )

    adoption["Average_Proficiency"] = (
        adoption["Average_Proficiency"].round(2)
    )

    adoption = adoption.sort_values(
        ["People", "Average_Proficiency"],
        ascending=False,
    )

    filter_dataframe(
        adoption,
        "skill_adoption",
        search_columns=["skill"],
    )

    # -------------------------
    # Common skills
    # -------------------------

    col1, col2 = st.columns(2)

    with col1:

        section_header("Most Represented Skills")

        common_skills = (
            person_skills["skill"]
            .value_counts()
            .head(10)
        )

        st.bar_chart(
            common_skills,
            height=320,
        )

    with col2:

        section_header("Project Skill Demand")

        demand = (
            project_skills["skill"]
            .value_counts()
            .head(10)
        )

        st.bar_chart(
            demand,
            height=320,
        )

    # -------------------------
    # Demand vs availability
    # -------------------------

    section_header(
        "Capability Demand vs Availability",
        "A simple descriptive comparison of project demand and employee availability.",
    )

    availability = (
        person_skills
        .groupby("skill")["person_id"]
        .nunique()
        .rename("Available People")
    )

    demand = (
        project_skills
        .groupby("skill")["project_id"]
        .nunique()
        .rename("Projects Requiring Skill")
    )

    demand_supply = pd.concat(
        [
            availability,
            demand,
        ],
        axis=1,
    ).fillna(0).reset_index()

    demand_supply["Availability per Project"] = (
        demand_supply["Available People"]
        /
        demand_supply["Projects Requiring Skill"].replace(0, 1)
    ).round(2)

    filter_dataframe(
        demand_supply,
        "skill_demand_supply",
        search_columns=["skill"],
    )

    st.caption(
        "This is a descriptive capability signal based on the current database records, "
        "not a forecast."
    )


# ============================================================
# ORGANISATION NETWORK
# ============================================================

def _embedding_map_dashboard(
    graph_data,
    retrieved_keys,
    relationship_types,
):
    """
    Create the GraphRAG embedding-space visualization used in the
    standalone GraphRAG application, adapted for the dashboard.
    """

    nodes = graph_data["nodes"]

    if not nodes:
        return None

    embeddings = np.asarray(
        [node["embedding"] for node in nodes],
        dtype=float,
    )

    centered = embeddings - embeddings.mean(axis=0)

    if len(nodes) > 1 and np.any(centered):
        _, _, components = np.linalg.svd(
            centered,
            full_matrices=False,
        )

        coordinates = centered @ components[:2].T
    else:
        coordinates = np.zeros((len(nodes), 2))

    if coordinates.shape[1] == 1:
        coordinates = np.column_stack(
            (
                coordinates,
                np.zeros(len(nodes)),
            )
        )

    positions = {}
    node_rows = []

    for node, (x, y) in zip(nodes, coordinates):

        key = (
            node["source_type"],
            node["source_id"],
        )

        positions[key] = (
            float(x),
            float(y),
        )

        node_rows.append(
            {
                "x": float(x),
                "y": float(y),
                "type": node["source_type"].title(),
                "shape": (
                    "diamond"
                    if key in retrieved_keys
                    else "circle"
                ),
                "label": node["label"],
                "content": node["content"],
                "retrieval": (
                    "Retrieved for latest question"
                    if key in retrieved_keys
                    else "Not in latest retrieval"
                ),
            }
        )

    edge_rows = []

    for edge in graph_data["edges"]:

        if edge["relation"] not in relationship_types:
            continue

        source = positions.get(
            edge["source"]
        )

        target = positions.get(
            edge["target"]
        )

        if source is None or target is None:
            continue

        edge_rows.append(
            {
                "x": source[0],
                "y": source[1],
                "x2": target[0],
                "y2": target[1],
                "relation": edge["relation"].title(),
                "details": edge["details"],
            }
        )

    points = (
        alt.Chart(
            pd.DataFrame(node_rows)
        )
        .mark_point(
            filled=True,
            size=110,
        )
        .encode(
            x=alt.X(
                "x:Q",
                title="PCA component 1",
            ),
            y=alt.Y(
                "y:Q",
                title="PCA component 2",
            ),
            color=alt.Color(
                "type:N",
                title="Entity type",
            ),
            shape=alt.Shape(
                "shape:N",
                title="Retrieval",
            ),
            tooltip=[
                alt.Tooltip(
                    "type:N",
                    title="Type",
                ),
                alt.Tooltip(
                    "label:N",
                    title="Name",
                ),
                alt.Tooltip(
                    "retrieval:N",
                    title="Latest retrieval",
                ),
                alt.Tooltip(
                    "content:N",
                    title="Embedded text",
                ),
            ],
        )
    )

    chart = points

    if edge_rows:

        edges = (
            alt.Chart(
                pd.DataFrame(edge_rows)
            )
            .mark_rule(
                opacity=0.4,
                strokeWidth=1.2,
            )
            .encode(
                x="x:Q",
                y="y:Q",
                x2="x2:Q",
                y2="y2:Q",
                tooltip=[
                    alt.Tooltip(
                        "relation:N",
                        title="Relationship",
                    ),
                    alt.Tooltip(
                        "details:N",
                        title="Details",
                    ),
                ],
            )
        )

        chart = edges + points

    return (
        chart
        .properties(
            height=430
        )
        .interactive()
    )


def _dot_escape(value):
    """
    Safely escape text used in Graphviz labels.
    """

    return (
        str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
    )


def show_network():

    # ========================================================
    # PAGE HEADER
    # ========================================================

    hero(
        "Organisation Network",
        "Explore collaboration patterns, employee relationships and the GraphRAG knowledge space.",
    )

    # ========================================================
    # LOAD PEOPLE
    # ========================================================

    people = read_sql(
        """
        SELECT
            person_id,
            name
        FROM capstone.person
        ORDER BY name
        """
    )

    # ========================================================
    # LOAD INTERACTIONS
    # ========================================================

    interactions = read_sql(
        """
        SELECT
            i.person_a,
            p1.name AS person_a_name,
            i.person_b,
            p2.name AS person_b_name,
            i.project_id,
            proj.title AS project,
            i.frequency,
            i.last_contact
        FROM capstone.interaction i

        JOIN capstone.person p1
            ON p1.person_id = i.person_a

        JOIN capstone.person p2
            ON p2.person_id = i.person_b

        LEFT JOIN capstone.project proj
            ON proj.project_id = i.project_id

        WHERE i.person_a IS NOT NULL
          AND i.person_b IS NOT NULL

        ORDER BY
            i.frequency DESC NULLS LAST
        """
    )

    # ========================================================
    # HANDLE EMPTY DATA
    # ========================================================

    if interactions.empty:

        unique_relationships = 0
        interaction_volume = 0

    else:

        # ----------------------------------------------------
        # Canonical employee pair
        # Treat A-B and B-A as the same relationship
        # ----------------------------------------------------

        interactions["person_1"] = interactions.apply(
            lambda row: min(
                str(row["person_a"]),
                str(row["person_b"]),
            ),
            axis=1,
        )

        interactions["person_2"] = interactions.apply(
            lambda row: max(
                str(row["person_a"]),
                str(row["person_b"]),
            ),
            axis=1,
        )

        unique_relationships = (
            interactions[
                [
                    "person_1",
                    "person_2",
                ]
            ]
            .drop_duplicates()
            .shape[0]
        )

        interaction_volume = int(
            interactions["frequency"]
            .fillna(0)
            .sum()
        )

    # ========================================================
    # KPI CARDS
    # ========================================================

    c1, c2, c3 = st.columns(3)

    with c1:

        metric_card(
            "People",
            len(people),
        )

    with c2:

        metric_card(
            "Relationships",
            unique_relationships,
        )

    with c3:

        metric_card(
            "Interaction Volume",
            interaction_volume,
        )

    # ========================================================
    # GRAPHRAG KNOWLEDGE MAP
    # ========================================================

    section_header(
        "GraphRAG Knowledge Map",
        "Explore semantic relationships between people and projects using the existing knowledge graph.",
    )

    try:

        graph_data = embedding_graph_data()

        if not graph_data["nodes"]:

            st.info(
                "No embeddings are currently available. "
                "Build or refresh embeddings from the GraphRAG application first."
            )

        else:

            retrieved_keys = set(
                st.session_state.get(
                    "rag_last_retrieved_keys",
                    [],
                )
            )

            selected_relations = st.multiselect(
                "Show relationship types",
                [
                    "assignment",
                    "interaction",
                ],
                default=[
                    "assignment",
                    "interaction",
                ],
                key="dashboard_embedding_relationships",
            )

            st.caption(
                "People and projects are positioned using PCA of their embeddings. "
                "Lines represent actual assignment or interaction relationships; "
                "they are not inferred from visual proximity."
            )

            graph = _embedding_map_dashboard(
                graph_data,
                retrieved_keys,
                selected_relations,
            )

            if graph is not None:

                left, center, right = st.columns(
                    [1, 3, 1]
                )

                with center:

                    st.altair_chart(
                        graph,
                        use_container_width=True,
                    )

            selected_edge_count = sum(
                edge["relation"]
                in selected_relations
                for edge in graph_data["edges"]
            )

            st.caption(
                f"Showing {len(graph_data['nodes'])} embedded entities "
                f"and {selected_edge_count} selected relationships."
            )

    except (
        psycopg2.Error,
        ValueError,
        RuntimeError,
    ) as error:

        st.error(
            f"Could not load the GraphRAG visualization: {error}"
        )

    # ========================================================
    # KEY COLLABORATION RELATIONSHIPS
    # ========================================================

    section_header(
        "Key Collaboration Relationships",
        "Recorded employee-to-employee collaboration links.",
    )

    if interactions.empty:

        st.info(
            "No collaboration relationships are currently recorded."
        )

    else:

        # ----------------------------------------------------
        # Aggregate relationships
        # ----------------------------------------------------

        relationship_display = (
            interactions
            .groupby(
                [
                    "person_1",
                    "person_2",
                ],
                as_index=False,
            )
            .agg(
                interaction_frequency=(
                    "frequency",
                    "sum",
                ),
                projects=(
                    "project",
                    lambda x: ", ".join(
                        sorted(
                            {
                                str(value)
                                for value in x
                                if pd.notna(value)
                            }
                        )
                    ),
                ),
            )
            .sort_values(
                "interaction_frequency",
                ascending=False,
            )
        )

        person_name_map = {}

        for _, row in interactions.iterrows():
            person_name_map[str(row["person_a"])] = row["person_a_name"]
            person_name_map[str(row["person_b"])] = row["person_b_name"]

        relationship_display["Person A"] = relationship_display[
            "person_1"
        ].map(person_name_map)

        relationship_display["Person B"] = relationship_display[
            "person_2"
        ].map(person_name_map)

        relationship_display = relationship_display[
            [
                "Person A",
                "Person B",
                "interaction_frequency",
                "projects",
            ]
        ].rename(
            columns={
                "interaction_frequency": "Interactions",
                "projects": "Projects",
            }
        )

        st.dataframe(
            relationship_display,
            use_container_width=True,
            hide_index=True,
        )

    # ========================================================
    # COLLABORATION NETWORK
    # ========================================================

    section_header(
        "Collaboration Network",
        "Visualise the recorded employee-to-employee relationships.",
    )

    if interactions.empty:

        st.info(
            "No interaction data is available."
        )

    else:

        network_size = st.selectbox(
            "Network view",
            [
                "Top 10 relationships",
                "All relationships",
            ],
            key="network_size",
        )

        # ----------------------------------------------------
        # Aggregate employee relationships
        # ----------------------------------------------------

        network_df = (
            interactions
            .groupby(
                [
                    "person_1",
                    "person_2",
                ],
                as_index=False,
            )
            .agg(
                frequency=(
                    "frequency",
                    "sum",
                )
            )
            .sort_values(
                "frequency",
                ascending=False,
            )
        )

        if network_size == "Top 10 relationships":

            network_df = (
                network_df
                .head(10)
            )

        # ----------------------------------------------------
        # Build Graphviz network
        # ----------------------------------------------------

        lines = [
            "graph G {",

            (
                'graph [bgcolor="#FFFFFF", '
                'overlap=false, splines=true, '
                'pad=0.3, nodesep=0.5, ranksep=0.5];'
            ),

            (
                'node [shape=box, '
                'style="rounded,filled", '
                'fontname="Arial", '
                'fontsize=10, '
                'margin="0.12,0.08"];'
            ),

            (
                'edge [fontname="Arial", '
                'fontsize=8, '
                'penwidth=1.2];'
            ),
        ]

        added_nodes = set()

        for _, row in network_df.iterrows():

            person_a = _dot_escape(
                person_name_map.get(
                    str(row["person_1"]),
                    str(row["person_1"]),
                )
            )

            person_b = _dot_escape(
                person_name_map.get(
                    str(row["person_2"]),
                    str(row["person_2"]),
                )
            )
            frequency = int(
                row["frequency"]
            )

            # ------------------------------------------------
            # Add nodes
            # ------------------------------------------------

            if person_a not in added_nodes:

                lines.append(
                    f'"{person_a}" '
                    f'[label="{person_a}"];'
                )

                added_nodes.add(
                    person_a
                )

            if person_b not in added_nodes:

                lines.append(
                    f'"{person_b}" '
                    f'[label="{person_b}"];'
                )

                added_nodes.add(
                    person_b
                )

            # ------------------------------------------------
            # Add relationship
            # ------------------------------------------------

            lines.append(
                f'"{person_a}" -- "{person_b}" '
                f'[label="{frequency}"];'
            )

        lines.append("}")

        # ----------------------------------------------------
        # Smaller centred graph
        # ----------------------------------------------------

        left, center, right = st.columns(
            [1.5, 2, 1.5]
        )

        with center:

            st.graphviz_chart(
                "\n".join(lines),
                use_container_width=True,
            )

        st.caption(
            "Edge labels represent recorded interaction frequency."
        )

    # ========================================================
    # COLLABORATION SIGNALS
    # ========================================================

    section_header(
        "Collaboration Signals",
        "Descriptive indicators derived from recorded collaboration data.",
    )

    if interactions.empty:

        st.info(
            "No collaboration signals are available."
        )

    else:

        # ====================================================
        # MOST CONNECTED PEOPLE
        # ====================================================

        connections = []

        for _, row in interactions.iterrows():

            connections.append(
                {
                    "Person": row["person_a_name"],
                    "Collaborator": row["person_b_name"],
                }
            )

            connections.append(
                {
                    "Person": row["person_b_name"],
                    "Collaborator": row["person_a_name"],
                }
            )

        connection_df = pd.DataFrame(
            connections
        )

        most_connected = (
            connection_df
            .drop_duplicates()
            .groupby("Person")
            .size()
            .reset_index(
                name="Unique Collaborators"
            )
            .sort_values(
                "Unique Collaborators",
                ascending=False,
            )
            .head(5)
        )

        # ====================================================
        # STRONGEST RECORDED LINKS
        # ====================================================

        strongest = (
            interactions
            .groupby(
                [
                    "person_1",
                    "person_2",
                ],
                as_index=False,
            )
            .agg(
                frequency=(
                    "frequency",
                    "sum",
                )
            )
            .sort_values(
                "frequency",
                ascending=False,
            )
            .head(5)
        )

        strongest["Person A"] = strongest[
            "person_1"
        ].map(person_name_map)

        strongest["Person B"] = strongest[
            "person_2"
        ].map(person_name_map)

        strongest = strongest[
            [
                "Person A",
                "Person B",
                "frequency",
            ]
        ].rename(
            columns={
                "frequency": "Interaction Frequency",
            }
        )

        
        # ====================================================
        # DISPLAY SIGNALS
        # ====================================================

        col1, col2 = st.columns(2)

        with col1:

            st.markdown(
                '<div class="insight-card">'
                '<div class="insight-title">'
                'Most Connected People'
                '</div>'
                '<div class="insight-text">'
                'Employees with the highest number of distinct recorded collaborators.'
                '</div>'
                '</div>',
                unsafe_allow_html=True,
            )

            st.dataframe(
                most_connected,
                use_container_width=True,
                hide_index=True,
            )

        with col2:

            st.markdown(
                '<div class="insight-card">'
                '<div class="insight-title">'
                'Strongest Recorded Links'
                '</div>'
                '<div class="insight-text">'
                'Employee pairs with the highest recorded interaction frequency.'
                '</div>'
                '</div>',
                unsafe_allow_html=True,
            )

            st.dataframe(
                strongest,
                use_container_width=True,
                hide_index=True,
            )


# ============================================================
# ASK INTELLIGENCE
# ============================================================

def show_ask():

    hero(
        "Ask Intelligence",
        "Ask natural-language questions across the organisation's people, projects and knowledge graph.",
    )

    st.markdown(
        """
        <style>

        /* --------------------------------------------------------
           ASK INTELLIGENCE INPUTS
           -------------------------------------------------------- */

        div[data-testid="stTextInput"] input {
            color: #222222 !important;
            -webkit-text-fill-color: #222222 !important;
        }

        div[data-testid="stTextArea"] textarea {
            color: #222222 !important;
            -webkit-text-fill-color: #222222 !important;
        }

        div[data-testid="stTextInput"] input::placeholder {
            color: #666666 !important;
            opacity: 1 !important;
        }

        div[data-testid="stTextArea"] textarea::placeholder {
            color: #666666 !important;
            opacity: 1 !important;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="answer-box">
            <div class="answer-title">Knowledge Retrieval</div>
            <div>
                Ask a question in natural language. The system searches the
                indexed organisational knowledge and returns relevant evidence
                together with related organisational context.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # Example Questions
    # --------------------------------------------------------

    section_header(
        "Example Questions",
        "Use these examples as a guide for questions you can ask.",
    )

    st.markdown("• Who has Python and machine learning skills?")
    st.markdown("• Who has experience relevant to fraud detection?")
    st.markdown("• Which people have SQL skills?")
    st.markdown("• What skills are required for the Payments Fraud Detection project?")
    st.markdown("• Who has worked on healthcare projects?")

    # --------------------------------------------------------
    # Custom Question
    # --------------------------------------------------------

    question = st.text_area(
        "Your question",
        placeholder=(
            "Ask something about people, projects, skills "
            "or organisational relationships..."
        ),
        height=110,
        key="ask_question",
    )

    ask_custom = st.button(
        "Ask Intelligence",
        type="primary",
    )

    # --------------------------------------------------------
    # Determine whether a NEW question was submitted
    # --------------------------------------------------------

    if ask_custom:

        question_to_ask = question.strip()

        if not question_to_ask:

            st.warning(
                "Please enter a question."
            )

            return

        # ----------------------------------------------------
        # Retrieval
        # ----------------------------------------------------

        try:

            from rag_backend import retrieve

            matches, graph_context = retrieve(
                question_to_ask,
                limit=7,
            )

        except Exception as exc:

            st.error(
                f"Knowledge retrieval could not be completed: {exc}"
            )

            return

        # Store the results in session state.
        # This keeps the answer visible when filters change.

        st.session_state["ask_submitted_question"] = question_to_ask
        st.session_state["ask_matches"] = matches
        st.session_state["ask_graph_context"] = graph_context

    else:

        # ----------------------------------------------------
        # Recover previous results after a Streamlit rerun
        # ----------------------------------------------------

        matches = st.session_state.get(
            "ask_matches"
        )

        graph_context = st.session_state.get(
            "ask_graph_context"
        )

        if matches is None:

            return

    # --------------------------------------------------------
    # Finding
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="answer-box">
            <div class="answer-title">Finding</div>
            <div>
                The following organisational records were identified as relevant
                to your question.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not matches:

        st.info(
            "No matching knowledge records were found."
        )

        return

    # --------------------------------------------------------
    # Relevant Knowledge
    # --------------------------------------------------------

    section_header(
        "Relevant Knowledge",
        "Evidence retrieved from the indexed organisational data.",
    )

    evidence_filter = st.selectbox(
        "Show evidence",
        ["All", "Person", "Project"],
        key="ask_evidence_filter",
    )

    filtered_matches = []

    for match in matches:

        source_type = str(
            match.get(
                "source_type",
                match.get("type", "Unknown"),
            )
        ).strip().lower()

        if evidence_filter == "All":

            filtered_matches.append(match)

        elif evidence_filter.lower() == source_type:

            filtered_matches.append(match)

    if filtered_matches:

        for index, match in enumerate(
            filtered_matches,
            start=1,
        ):

            source_type = match.get(
                "source_type",
                match.get("type", "Unknown"),
            )

            similarity = round(
                float(
                    match.get(
                        "similarity",
                        0,
                    )
                ),
                3,
            )

            content = match.get(
                "content",
                str(match),
            )

            st.markdown(
                f"### #{index} · {str(source_type).upper()}"
            )

            st.caption(
                f"Similarity: {similarity}"
            )

            st.write(content)

            with st.expander(
                "View full evidence",
                expanded=False,
            ):

                st.write(content)

            st.divider()

    else:

        st.info(
            f"No {evidence_filter.lower()} evidence was found for this question."
        )

    # --------------------------------------------------------
    # Organisational Context
    # --------------------------------------------------------

    section_header(
        "Organisational Context",
        "Related people, projects and relationships returned by the knowledge graph.",
    )

    if graph_context:

        if isinstance(graph_context, str):

            st.write(graph_context)

        elif isinstance(graph_context, list):

            context_rows = []

            for item in graph_context:

                if isinstance(item, dict):

                    context_rows.append(item)

                else:

                    context_rows.append(
                        {
                            "Context": str(item)
                        }
                    )

            if context_rows:

                context_df = pd.DataFrame(
                    context_rows
                )

                st.dataframe(
                    context_df,
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "No organisational context was returned."
                )

        else:

            st.write(graph_context)

    else:

        st.info(
            "No additional organisational context was returned."
        )

    st.caption(
        "Ask Intelligence currently provides retrieval-based evidence and "
        "organisational context. It does not claim to make predictions or decisions."
    )


# ============================================================
# REPORT CENTRE
# ============================================================

def dataframe_to_html(df, max_rows=500):

    if df is None or df.empty:
        return "<p>No data available.</p>"

    display_df = df.head(max_rows).copy()

    return display_df.to_html(
        index=False,
        border=0,
        classes="report-table",
        escape=True,
    )


def build_report(
    sections,
    title,
    people,
    projects,
    skills,
    assignments,
    person_skills,
    project_skills,
    interactions,
):

    generated = datetime.now().strftime(
        "%d %B %Y, %I:%M %p"
    )

    html_parts = [
        """
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <title>Organisation Intelligence Report</title>

        <style>

        body {
            font-family: Arial, sans-serif;
            margin: 40px;
            color: #242124;
            background: #ffffff;
        }

        h1 {
            color: #6B1E2E;
            margin-bottom: 5px;
        }

        h2 {
            color: #6B1E2E;
            margin-top: 35px;
            border-bottom: 2px solid #E4DCDD;
            padding-bottom: 8px;
        }

        h3 {
            color: #531622;
            margin-top: 24px;
        }

        .subtitle {
            color: #6F6868;
            margin-bottom: 30px;
        }

        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin: 20px 0;
        }

        .kpi {
            border: 1px solid #E4DCDD;
            border-radius: 10px;
            padding: 15px;
            background: #F7F4F1;
        }

        .kpi-label {
            font-size: 12px;
            color: #6F6868;
        }

        .kpi-value {
            font-size: 24px;
            font-weight: bold;
            color: #6B1E2E;
            margin-top: 5px;
        }

        .report-table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0 25px 0;
            font-size: 12px;
        }

        .report-table th {
            background: #6B1E2E;
            color: white;
            padding: 8px;
            text-align: left;
        }

        .report-table td {
            border: 1px solid #E4DCDD;
            padding: 8px;
        }

        .report-table tr:nth-child(even) {
            background: #F7F4F1;
        }

        .page-break {
            page-break-before: always;
        }

        @media print {

            body {
                margin: 15mm;
            }

            .no-print {
                display: none;
            }

        }

        </style>

        </head>
        <body>
        """,
        f"<h1>{html.escape(title)}</h1>",
        f'<div class="subtitle">Generated {html.escape(generated)}</div>',
    ]

    # ========================================================
    # Executive Summary
    # ========================================================

    if "Executive Summary" in sections:

        html_parts.append("<h2>Executive Summary</h2>")

        html_parts.append(
            f"""
            <div class="kpi-grid">

                <div class="kpi">
                    <div class="kpi-label">People</div>
                    <div class="kpi-value">{len(people)}</div>
                </div>

                <div class="kpi">
                    <div class="kpi-label">Skills</div>
                    <div class="kpi-value">{len(skills)}</div>
                </div>

                <div class="kpi">
                    <div class="kpi-label">Projects</div>
                    <div class="kpi-value">{len(projects)}</div>
                </div>

                <div class="kpi">
                    <div class="kpi-label">Assignments</div>
                    <div class="kpi-value">{len(assignments)}</div>
                </div>

            </div>
            """
        )

    # ========================================================
    # People
    # ========================================================

    if "People Overview" in sections:

        html_parts.append("<h2>People Overview</h2>")

        html_parts.append(
            dataframe_to_html(
                people[
                    [
                        "name",
                        "department",
                        "role",
                        "joined_date",
                    ]
                ]
            )
        )

    if "Detailed Employee Skills" in sections:

        html_parts.append("<h2>Employee Skills</h2>")

        html_parts.append(
            dataframe_to_html(
                person_skills[
                    [
                        "person",
                        "skill",
                        "category",
                        "proficiency",
                        
                    ]
                ]
            )
        )

    # ========================================================
    # Projects
    # ========================================================

    if "Project Portfolio" in sections:

        html_parts.append("<h2>Project Portfolio</h2>")

        html_parts.append(
            dataframe_to_html(
                projects[
                    [
                        "project",
                        "domain",
                        "client_type",
                        "outcome",
                        "start_date",
                        "end_date",
                    ]
                ]
            )
        )

    if "Project Teams" in sections:

        html_parts.append("<h2>Project Teams</h2>")

        html_parts.append(
            dataframe_to_html(
                assignments[
                    [
                        "person",
                        "project",
                    ]
                ]
            )
        )

    if "Project Skill Coverage" in sections:

        html_parts.append("<h2>Project Skill Requirements</h2>")

        html_parts.append(
            dataframe_to_html(
                project_skills[
                    [
                        "project",
                        "skill",
                        "category",
                        "importance",
                    ]
                ]
            )
        )

    # ========================================================
    # Skills
    # ========================================================

    if "Skill Inventory" in sections:

        html_parts.append("<h2>Skill Inventory</h2>")

        html_parts.append(
            dataframe_to_html(
                skills[
                    [
                        "skill",
                        "category",
                    ]
                ]
            )
        )

    if "Skill Demand & Availability" in sections:

        availability = (
            person_skills
            .groupby("skill")["person_id"]
            .nunique()
            .rename("Available People")
        )

        demand = (
            project_skills
            .groupby("skill")["project_id"]
            .nunique()
            .rename("Projects Requiring Skill")
        )

        demand_supply = pd.concat(
            [
                availability,
                demand,
            ],
            axis=1,
        ).fillna(0).reset_index()

        demand_supply["Availability per Project"] = (
            demand_supply["Available People"]
            /
            demand_supply["Projects Requiring Skill"].replace(
                0,
                1,
            )
        ).round(2)

        html_parts.append(
            "<h2>Skill Demand & Availability</h2>"
        )

        html_parts.append(
            dataframe_to_html(
                demand_supply
            )
        )

    # ========================================================
    # Organisation
    # ========================================================

    if "Collaboration Summary" in sections:

        html_parts.append(
            "<h2>Collaboration Summary</h2>"
        )

        html_parts.append(
            dataframe_to_html(
                interactions[
                    [
                        "person_a",
                        "person_b",
                        "project",
                        "channel",
                        "frequency",
                        "last_contact",
                    ]
                ]
            )
        )

    # ========================================================
    # Analysis
    # ========================================================

    if "Capability Gaps" in sections:

        html_parts.append(
            "<h2>Capability Gaps</h2>"
        )

        gap_rows = []

        for project_id, project_group in project_skills.groupby(
            "project_id"
        ):

            project_name = project_group["project"].iloc[0]

            team_ids = set(
                assignments[
                    assignments["project_id"] == project_id
                ]["person_id"]
            )

            team_skills = set(
                person_skills[
                    person_skills["person_id"].isin(team_ids)
                ]["skill"]
                .astype(str)
                .str.lower()
            )

            for _, row in project_group.iterrows():

                if (
                    str(row["skill"]).lower()
                    not in team_skills
                ):

                    gap_rows.append(
                        {
                            "Project": project_name,
                            "Skill": row["skill"],
                            "Importance": row["importance"],
                        }
                    )

        gap_df = pd.DataFrame(gap_rows)

        html_parts.append(
            dataframe_to_html(gap_df)
        )

    # ========================================================
    # Methodology
    # ========================================================

    if "Methodology & Data Notes" in sections:

        html_parts.append(
            """
            <h2>Methodology & Data Notes</h2>

            <p>
            This report is generated from the organisation's current
            knowledge-management database.
            </p>

            <p>
            Capability coverage is based on recorded project requirements
            and employee skill records. Demand and availability indicators
            are descriptive and should not be interpreted as predictive
            machine-learning outputs.
            </p>

            <p>
            The report reflects the information currently stored in the
            system and may not capture informal or unrecorded organisational
            knowledge.
            </p>
            """
        )

    html_parts.append(
        """
        <div style="margin-top:50px;color:#6F6868;font-size:11px;">
            Organisation Intelligence System · BDM Capstone
        </div>
        </body>
        </html>
        """
    )

    return "\n".join(html_parts)


def show_reports():

    people = load_people()
    projects = load_projects()
    skills = load_skills()
    assignments = load_assignments()
    person_skills = load_person_skills()
    project_skills = load_project_skills()
    interactions = load_interactions()

    hero(
        "Report Centre",
        "Build a customised management report using the organisation's current intelligence.",
    )

    # -------------------------
    # KPIs
    # -------------------------

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card("People", len(people))

    with c2:
        metric_card("Projects", len(projects))

    with c3:
        metric_card("Skills", len(skills))

    with c4:
        metric_card("Relationships", len(interactions))

    # -------------------------
    # Report builder
    # -------------------------

    section_header(
        "Report Builder",
        "Choose exactly which sections should appear in the generated report.",
    )

    report_title = st.text_input(
        "Report title",
        value="Organisation Intelligence Report",
    )

    st.markdown("### Executive")

    executive_sections = st.multiselect(
        "Executive sections",
        [
            "Executive Summary",
        ],
        default=[
            "Executive Summary",
        ],
        key="report_exec",
    )

    st.markdown("### People")

    people_sections = st.multiselect(
        "People sections",
        [
            "People Overview",
            "Detailed Employee Skills",
        ],
        default=[
            "People Overview",
        ],
        key="report_people",
    )

    st.markdown("### Projects")

    project_sections = st.multiselect(
        "Project sections",
        [
            "Project Portfolio",
            "Project Teams",
            "Project Skill Coverage",
        ],
        default=[
            "Project Portfolio",
            "Project Skill Coverage",
        ],
        key="report_projects",
    )

    st.markdown("### Skills")

    skill_sections = st.multiselect(
        "Skill sections",
        [
            "Skill Inventory",
            "Skill Demand & Availability",
        ],
        default=[
            "Skill Inventory",
        ],
        key="report_skills",
    )

    st.markdown("### Organisation")

    organisation_sections = st.multiselect(
        "Organisation sections",
        [
            "Collaboration Summary",
        ],
        default=[],
        key="report_org",
    )

    st.markdown("### Analysis")

    analysis_sections = st.multiselect(
        "Analysis sections",
        [
            "Capability Gaps",
            "Methodology & Data Notes",
        ],
        default=[
            "Capability Gaps",
            "Methodology & Data Notes",
        ],
        key="report_analysis",
    )

    selected_sections = (
        executive_sections
        + people_sections
        + project_sections
        + skill_sections
        + organisation_sections
        + analysis_sections
    )

    st.divider()

    st.info(
        f"{len(selected_sections)} report sections selected."
    )

    # -------------------------
    # Generate
    # -------------------------

    if st.button(
        "Generate Report",
        type="primary",
    ):

        if not selected_sections:
            st.warning(
                "Select at least one report section."
            )
            return

        report_html = build_report(
            sections=selected_sections,
            title=report_title,
            people=people,
            projects=projects,
            skills=skills,
            assignments=assignments,
            person_skills=person_skills,
            project_skills=project_skills,
            interactions=interactions,
        )

        st.session_state.report_html = report_html
        st.session_state.report_title = report_title

    # -------------------------
    # Preview
    # -------------------------

    if "report_html" in st.session_state:

        section_header(
            "Report Preview",
            "Review the generated report before downloading or printing it.",
        )

        components.html(
            st.session_state.report_html,
            height=900,
            scrolling=True,
        )

        report_bytes = (
            st.session_state.report_html
            .encode("utf-8")
        )

        st.download_button(
            "Download HTML Report",
            report_bytes,
            file_name="organisation_intelligence_report.html",
            mime="text/html",
        )

        st.markdown(
            """
            <div class="insight-card">
                <div class="insight-title">Printing</div>
                <div class="insight-text">
                    Open the downloaded HTML report in your browser and use
                    Print → Save as PDF if a PDF copy is required.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# MAIN ROUTER
# ============================================================

if page == "Executive Overview":
    show_overview()

elif page == "People Intelligence":
    show_people()

elif page == "Project Intelligence":
    show_projects()

elif page == "Skills Intelligence":
    show_skills()

elif page == "Organisation Network":
    show_network()

elif page == "Ask Intelligence":
    show_ask()

elif page == "Report Centre":
    show_reports()