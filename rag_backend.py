"""PostgreSQL-backed embedding, vector retrieval, and relational graph expansion."""

from contextlib import closing
from functools import lru_cache
import os

import psycopg2
from fastembed import TextEmbedding
from pgvector import Vector
from pgvector.psycopg2 import register_vector
from psycopg2.extras import execute_values


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384


def database_url():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL is not set. Add it to the project .env file.")
    return url


@lru_cache(maxsize=1)
def embedding_model():
    return TextEmbedding(model_name=MODEL_NAME)


def _fetch_documents(connection):
    documents = []
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT p.person_id, p.name, p.department, p.role,
                   p.joined_date::text,
                   COALESCE((
                       SELECT string_agg(
                           s.name || ' (proficiency ' || ps.proficiency || '/5)',
                           ', ' ORDER BY s.name
                       )
                       FROM capstone.person_skill ps
                       JOIN capstone.skill s ON s.skill_id = ps.skill_id
                       WHERE ps.person_id = p.person_id
                   ), 'No recorded skills') AS skills,
                   COALESCE((
                       SELECT string_agg(
                           proj.title || ' (' || COALESCE(proj.domain, 'domain not recorded')
                           || ') as ' || a.role_played,
                           ', ' ORDER BY proj.title
                       )
                       FROM capstone.assignment a
                       JOIN capstone.project proj ON proj.project_id = a.project_id
                       WHERE a.person_id = p.person_id
                   ), 'No recorded project assignments') AS projects
            FROM capstone.person p
            ORDER BY p.person_id
            """
        )
        people = cursor.fetchall()

        cursor.execute(
            """
            SELECT proj.project_id, proj.title, proj.domain, proj.outcome,
                   proj.client_type, proj.start_date::text, proj.end_date::text,
                   COALESCE((
                       SELECT string_agg(
                           s.name || ' (' || ps.importance || ')',
                           ', ' ORDER BY s.name
                       )
                       FROM capstone.project_skill ps
                       JOIN capstone.skill s ON s.skill_id = ps.skill_id
                       WHERE ps.project_id = proj.project_id
                   ), 'No recorded skills') AS skills,
                   COALESCE((
                       SELECT string_agg(
                           p.name || ' as ' || a.role_played,
                           ', ' ORDER BY p.name
                       )
                       FROM capstone.assignment a
                       JOIN capstone.person p ON p.person_id = a.person_id
                       WHERE a.project_id = proj.project_id
                   ), 'No recorded team assignments')
            FROM capstone.project proj
            ORDER BY proj.project_id
            """
        )
        projects = cursor.fetchall()

    for person_id, name, department, role, joined_date, skills, assignments in people:
        content = (
            f"Person: {name}. Department: {department or 'not recorded'}. "
            f"Role: {role or 'not recorded'}. Joined: {joined_date or 'not recorded'}. "
            f"Skills: {skills}. Project assignments: {assignments}."
        )
        documents.append(("person", person_id, content))

    for project_id, title, domain, outcome, client_type, start_date, end_date, skills, team in projects:
        content = (
            f"Project: {title}. Domain: {domain or 'not recorded'}. "
            f"Outcome: {outcome or 'not recorded'}. Client type: {client_type or 'not recorded'}. "
            f"Dates: {start_date or 'not recorded'} to {end_date or 'ongoing'}. "
            f"Required and preferred skills: {skills}. Team and roles: {team}."
        )
        documents.append(("project", project_id, content))

    return documents


def rebuild_embeddings():
    """Rebuild the derived vector records atomically from current relational data."""
    with closing(psycopg2.connect(database_url())) as connection, connection:
        documents = _fetch_documents(connection)

    if not documents:
        raise ValueError(
            "No people or projects were found. Create the capstone tables and seed data first."
        )

    vectors = list(embedding_model().embed([document[2] for document in documents]))
    if len(vectors) != len(documents):
        raise RuntimeError("The embedding model returned an incomplete result set.")
    if any(len(vector) != EMBEDDING_DIMENSIONS for vector in vectors):
        raise RuntimeError(
            f"The embedding model must return {EMBEDDING_DIMENSIONS}-dimensional vectors."
        )
    records = [
        (source_type, source_id, content, Vector(vector), MODEL_NAME)
        for (source_type, source_id, content), vector in zip(documents, vectors)
    ]

    with closing(psycopg2.connect(database_url())) as connection, connection:
        with connection.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            register_vector(connection)
            cursor.execute("CREATE SCHEMA IF NOT EXISTS capstone")
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS capstone.knowledge_embedding (
                    embedding_id BIGSERIAL PRIMARY KEY,
                    source_type TEXT NOT NULL CHECK (source_type IN ('person', 'project')),
                    source_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    embedding vector({EMBEDDING_DIMENSIONS}) NOT NULL,
                    model_name TEXT NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE (source_type, source_id)
                )
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS knowledge_embedding_cosine_idx
                ON capstone.knowledge_embedding
                USING hnsw (embedding vector_cosine_ops)
                """
            )
            cursor.execute("DELETE FROM capstone.knowledge_embedding")
            execute_values(
                cursor,
                """
                INSERT INTO capstone.knowledge_embedding
                    (source_type, source_id, content, embedding, model_name)
                VALUES %s
                """,
                records,
            )
    return len(records)


def embedding_status():
    with closing(psycopg2.connect(database_url())) as connection, connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('capstone.knowledge_embedding')")
            if cursor.fetchone()[0] is None:
                return {"total": 0, "by_model": []}
            cursor.execute(
                """
                SELECT COUNT(*), COALESCE(
                    json_agg(json_build_object('model', model_name, 'count', count)),
                    '[]'::json
                )
                FROM (
                    SELECT model_name, COUNT(*) AS count
                    FROM capstone.knowledge_embedding
                    GROUP BY model_name
                    ORDER BY model_name
                ) models
                """
            )
            total, by_model = cursor.fetchone()
    return {"total": total, "by_model": by_model}


def embedding_graph_data():
    """Return indexed entities and their actual person/project relationships."""
    with closing(psycopg2.connect(database_url())) as connection, connection:
        register_vector(connection)
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('capstone.knowledge_embedding')")
            if cursor.fetchone()[0] is None:
                return {"nodes": [], "edges": []}

            cursor.execute(
                """
                SELECT ke.source_type, ke.source_id,
                       CASE
                           WHEN ke.source_type = 'person' THEN p.name
                           ELSE proj.title
                       END AS label,
                       ke.content, ke.embedding
                FROM capstone.knowledge_embedding ke
                LEFT JOIN capstone.person p
                  ON ke.source_type = 'person' AND p.person_id = ke.source_id
                LEFT JOIN capstone.project proj
                  ON ke.source_type = 'project' AND proj.project_id = ke.source_id
                WHERE ke.model_name = %s
                  AND (
                      (ke.source_type = 'person' AND p.person_id IS NOT NULL)
                      OR (ke.source_type = 'project' AND proj.project_id IS NOT NULL)
                  )
                ORDER BY ke.source_type, ke.source_id
                """,
                (MODEL_NAME,),
            )
            nodes = [
                {
                    "source_type": source_type,
                    "source_id": source_id,
                    "label": label,
                    "content": content,
                    "embedding": embedding.to_list(),
                }
                for source_type, source_id, label, content, embedding in cursor.fetchall()
            ]
            node_keys = {
                (node["source_type"], node["source_id"])
                for node in nodes
            }

            cursor.execute(
                """
                SELECT p.person_id, proj.project_id,
                       string_agg(DISTINCT a.role_played, ', ' ORDER BY a.role_played)
                FROM capstone.assignment a
                JOIN capstone.person p ON p.person_id = a.person_id
                JOIN capstone.project proj ON proj.project_id = a.project_id
                GROUP BY p.person_id, proj.project_id
                ORDER BY p.person_id, proj.project_id
                """
            )
            edges = [
                {
                    "source": ("person", person_id),
                    "target": ("project", project_id),
                    "relation": "assignment",
                    "details": f"Roles: {roles or 'not recorded'}",
                }
                for person_id, project_id, roles in cursor.fetchall()
                if ("person", person_id) in node_keys
                and ("project", project_id) in node_keys
            ]

            cursor.execute(
                """
                SELECT LEAST(person_a, person_b), GREATEST(person_a, person_b),
                       SUM(frequency), COUNT(*),
                       string_agg(DISTINCT proj.title, ', ' ORDER BY proj.title)
                FROM capstone.interaction i
                JOIN capstone.project proj ON proj.project_id = i.project_id
                WHERE person_a IS NOT NULL AND person_b IS NOT NULL
                GROUP BY LEAST(person_a, person_b), GREATEST(person_a, person_b)
                ORDER BY LEAST(person_a, person_b), GREATEST(person_a, person_b)
                """
            )
            edges.extend(
                {
                    "source": ("person", person_a),
                    "target": ("person", person_b),
                    "relation": "interaction",
                    "details": (
                        f"{frequency} interactions across {interaction_count} records; "
                        f"projects: {projects or 'not recorded'}"
                    ),
                }
                for person_a, person_b, frequency, interaction_count, projects
                in cursor.fetchall()
                if ("person", person_a) in node_keys
                and ("person", person_b) in node_keys
            )

    return {"nodes": nodes, "edges": edges}


def _person_graph_context(cursor, person_id):
    cursor.execute(
        """
        SELECT p.name, p.department, p.role,
               COALESCE((
                   SELECT string_agg(s.name, ', ' ORDER BY s.name)
                   FROM capstone.person_skill ps
                   JOIN capstone.skill s ON s.skill_id = ps.skill_id
                   WHERE ps.person_id = p.person_id
               ), 'none recorded'),
               COALESCE((
                   SELECT string_agg(
                       proj.title || ' (' || COALESCE(proj.domain, 'domain not recorded')
                       || ', ' || a.role_played || ')',
                       ', ' ORDER BY proj.title
                   )
                   FROM capstone.assignment a
                   JOIN capstone.project proj ON proj.project_id = a.project_id
                   WHERE a.person_id = p.person_id
               ), 'none recorded'),
               COALESCE((
                   SELECT string_agg(DISTINCT other.name || ' via ' || proj.title, ', ' ORDER BY other.name || ' via ' || proj.title)
                   FROM capstone.interaction i
                   JOIN capstone.person other
                     ON other.person_id = CASE
                         WHEN i.person_a = p.person_id THEN i.person_b
                         ELSE i.person_a
                     END
                   JOIN capstone.project proj ON proj.project_id = i.project_id
                   WHERE i.person_a = p.person_id OR i.person_b = p.person_id
               ), 'none recorded')
        FROM capstone.person p
        WHERE p.person_id = %s
        """,
        (person_id,),
    )
    row = cursor.fetchone()
    if row is None:
        return None
    name, department, role, skills, projects, collaborators = row
    return (
        f"Person graph node {name} (department: {department or 'not recorded'}; "
        f"role: {role or 'not recorded'}). Skill edges: {skills}. "
        f"Assignment-to-project edges: {projects}. Interaction-to-person/project edges: {collaborators}."
    )


def _project_graph_context(cursor, project_id):
    cursor.execute(
        """
        SELECT proj.title, proj.domain,
               COALESCE((
                   SELECT string_agg(s.name || ' (' || ps.importance || ')', ', ' ORDER BY s.name)
                   FROM capstone.project_skill ps
                   JOIN capstone.skill s ON s.skill_id = ps.skill_id
                   WHERE ps.project_id = proj.project_id
               ), 'none recorded'),
               COALESCE((
                   SELECT string_agg(
                       p.name || ' (' || a.role_played || '; skills: ' || COALESCE((
                           SELECT string_agg(
                               s.name || ' (proficiency ' || ps.proficiency || '/5)',
                               ', ' ORDER BY s.name
                           )
                           FROM capstone.person_skill ps
                           JOIN capstone.skill s ON s.skill_id = ps.skill_id
                           WHERE ps.person_id = p.person_id
                       ), 'none recorded') || ')',
                       ', ' ORDER BY p.name
                   )
                   FROM capstone.assignment a
                   JOIN capstone.person p ON p.person_id = a.person_id
                   WHERE a.project_id = proj.project_id
               ), 'none recorded'),
               COALESCE((
                   SELECT string_agg(
                       DISTINCT p1.name || ' - ' || p2.name || ' (' || i.frequency || ' ' || i.channel || ' interactions)',
                       '; '
                   )
                   FROM capstone.interaction i
                   JOIN capstone.person p1 ON p1.person_id = i.person_a
                   JOIN capstone.person p2 ON p2.person_id = i.person_b
                   WHERE i.project_id = proj.project_id
               ), 'none recorded')
        FROM capstone.project proj
        WHERE proj.project_id = %s
        """,
        (project_id,),
    )
    row = cursor.fetchone()
    if row is None:
        return None
    title, domain, skills, team, interactions = row
    return (
        f"Project graph node {title} (domain: {domain or 'not recorded'}). "
        f"Required/preferred skill edges: {skills}. Assignment-to-person edges: {team}. "
        f"Interaction edges in this project: {interactions}."
    )


def retrieve(question, limit=5):
    if not question.strip():
        raise ValueError("Enter a question before searching.")

    query_vector = next(embedding_model().embed([question]))
    with closing(psycopg2.connect(database_url())) as connection, connection:
        register_vector(connection)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT source_type, source_id, content,
                       1 - (embedding <=> %s) AS similarity
                FROM capstone.knowledge_embedding
                ORDER BY embedding <=> %s
                LIMIT %s
                """,
                (Vector(query_vector), Vector(query_vector), limit),
            )
            matches = cursor.fetchall()

            graph_context = []
            seen = set()
            for source_type, source_id, _, _ in matches:
                source = (source_type, source_id)
                if source in seen:
                    continue
                seen.add(source)
                context = (
                    _person_graph_context(cursor, source_id)
                    if source_type == "person"
                    else _project_graph_context(cursor, source_id)
                )
                if context:
                    graph_context.append(context)

    return [
        {
            "source_type": source_type,
            "source_id": source_id,
            "content": content,
            "similarity": float(similarity),
        }
        for source_type, source_id, content, similarity in matches
    ], graph_context


def format_evidence(matches, graph_context):
    evidence = []
    for match in matches:
        evidence.append(
            f"[{match['source_type']}:{match['source_id']}] {match['content']}"
        )
    evidence.extend(f"[relational graph] {item}" for item in graph_context)
    return "\n".join(evidence)
