"""Streamlit teaching application for PostgreSQL and Graph RAG."""

import os
from pathlib import Path

import altair as alt
from dotenv import load_dotenv
from groq import APIError, Groq
import numpy as np
import pandas as pd
import psycopg2
import streamlit as st

from rag_backend import (
    EMBEDDING_DIMENSIONS,
    MODEL_NAME,
    database_url,
    embedding_graph_data,
    embedding_status,
    format_evidence,
    rebuild_embeddings,
    retrieve,
)


def _dot_escape(value):
    return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _retrieval_graph(question, matches, graph_context):
    question_label = _dot_escape(f"Question\n{question}")
    lines = [
        "digraph retrieval {",
        '  graph [rankdir=LR, bgcolor="transparent", nodesep=0.45, ranksep=0.7];',
        '  node [shape=box, style="rounded,filled", fontname="Arial", color="#94a3b8"];',
        '  edge [fontname="Arial", fontsize=10, color="#64748b"];',
        f'  question [label="{question_label}", fillcolor="#dbeafe"];',
        '  search [label="Vector search\\npgvector cosine similarity", fillcolor="#e0e7ff"];',
        '  question -> search [label="embed"];',
    ]
    for index, match in enumerate(matches):
        seed_id = f"seed_{index}"
        label = (
            f"{match['source_type'].title()} #{match['source_id']}"
            f"\nsimilarity {match['similarity']:.3f}"
        )
        lines.append(f'  {seed_id} [label="{_dot_escape(label)}", fillcolor="#fef3c7"];')
        lines.append(f'  search -> {seed_id} [label="top match"];')

    for index, context in enumerate(graph_context):
        if context.startswith("Person graph node "):
            entity_type = "Person"
            name = context[len("Person graph node "):].partition(" (department:")[0]
        elif context.startswith("Project graph node "):
            entity_type = "Project"
            name = context[len("Project graph node "):].partition(" (domain:")[0]
        else:
            entity_type, name = "Relational record", str(index + 1)

        seed_index = next(
            (
                i for i, match in enumerate(matches)
                if match["source_type"] == entity_type.lower()
                and match["content"].startswith(f"{entity_type}: {name}.")
            ),
            None,
        )
        context_id = f"context_{index}"
        context_label = _dot_escape(f"{entity_type}\n{name}")
        lines.append(
            f'  {context_id} [label="{context_label}", '
            'fillcolor="#dcfce7"];'
        )
        if seed_index is not None:
            lines.append(f'  seed_{seed_index} -> {context_id} [label="SQL joins"];')
        else:
            lines.append(f'  search -> {context_id} [label="relational expansion"];')

    if not graph_context:
        lines.append(
            '  no_context [label="No connected relational records", fillcolor="#f1f5f9"];'
        )
        lines.append("  search -> no_context;")
    lines.append("}")
    return "\n".join(lines)


def _embedding_map(graph_data, retrieved_keys, relationship_types):
    nodes = graph_data["nodes"]
    embeddings = np.asarray([node["embedding"] for node in nodes], dtype=float)
    centered = embeddings - embeddings.mean(axis=0)
    if len(nodes) > 1 and np.any(centered):
        _, _, components = np.linalg.svd(centered, full_matrices=False)
        coordinates = centered @ components[:2].T
    else:
        coordinates = np.zeros((len(nodes), 2))
    if coordinates.shape[1] == 1:
        coordinates = np.column_stack((coordinates, np.zeros(len(nodes))))

    positions = {}
    node_rows = []
    for node, (x, y) in zip(nodes, coordinates):
        key = (node["source_type"], node["source_id"])
        positions[key] = (float(x), float(y))
        node_rows.append(
            {
                "x": float(x),
                "y": float(y),
                "type": node["source_type"].title(),
                "shape": "diamond" if key in retrieved_keys else "circle",
                "label": node["label"],
                "id": node["source_id"],
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
        source = positions.get(edge["source"])
        target = positions.get(edge["target"])
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

    points = alt.Chart(pd.DataFrame(node_rows)).mark_point(filled=True, size=150).encode(
        x=alt.X("x:Q", title="PCA component 1"),
        y=alt.Y("y:Q", title="PCA component 2"),
        color=alt.Color("type:N", title="Entity type"),
        shape=alt.Shape("shape:N", title="Retrieval highlight"),
        tooltip=[
            alt.Tooltip("type:N", title="Type"),
            alt.Tooltip("label:N", title="Name"),
            alt.Tooltip("id:Q", title="ID"),
            alt.Tooltip("retrieval:N", title="Latest retrieval"),
            alt.Tooltip("content:N", title="Embedded text"),
        ],
    )
    chart = points
    if edge_rows:
        edges = alt.Chart(pd.DataFrame(edge_rows)).mark_rule(
            color="#94a3b8", opacity=0.45, strokeWidth=1.5
        ).encode(
            x="x:Q",
            y="y:Q",
            x2="x2:Q",
            y2="y2:Q",
            tooltip=[
                alt.Tooltip("relation:N", title="Relationship"),
                alt.Tooltip("details:N", title="Details"),
            ],
        )
        chart = edges + points
    return chart.properties(height=520).interactive()


load_dotenv(override=True)
st.set_page_config(page_title="Organizational Knowledge Graph RAG", page_icon="🧭", layout="wide")

st.title("Organizational Knowledge Graph RAG")
st.caption(
    "A Business Data Management walkthrough: turn relational organizational knowledge "
    "into searchable vectors, follow its relationships, and generate evidence-grounded answers."
)

overview_tab, ingest_tab, ask_tab = st.tabs(
    ["How it works & ERD", "Build embeddings", "Ask the knowledge graph"]
)

with overview_tab:
    st.header("From business data to a grounded answer")
    stages = st.columns(5)
    stage_text = [
        ("1 · Relational data", "People, skills, projects, assignments, and collaboration metadata live in normalized PostgreSQL tables."),
        ("2 · Prepare documents", "SQL joins turn each person and project into a compact, readable knowledge record."),
        ("3 · Embed & store", f"Local {MODEL_NAME} makes {EMBEDDING_DIMENSIONS}-dimensional vectors, stored in PostgreSQL with pgvector."),
        ("4 · Retrieve & expand", "Cosine similarity finds likely records; SQL follows person, skill, project, assignment, and interaction edges."),
        ("5 · Generate", "Retrieved evidence is sent to Groq when you provide an API key; answers are grounded in those records."),
    ]
    for column, (heading, description) in zip(stages, stage_text):
        with column:
            st.markdown(f"**{heading}**")
            st.write(description)

    st.subheader("See the difference: standard RAG vs this Graph RAG")
    standard_column, graph_column = st.columns(2)
    with standard_column:
        st.markdown("**Standard RAG**")
        st.graphviz_chart(
            """
            digraph standard_rag {
              graph [rankdir=LR, bgcolor="transparent"];
              node [shape=box, style="rounded,filled", fontname="Arial", color="#94a3b8"];
              edge [fontname="Arial", fontsize=10, color="#64748b"];
              question [label="Question", fillcolor="#dbeafe"];
              vectors [label="Vector search", fillcolor="#e0e7ff"];
              chunks [label="Top matching\\ntext chunks", fillcolor="#fef3c7"];
              answer [label="LLM answer", fillcolor="#fce7f3"];
              question -> vectors -> chunks -> answer;
            }
            """,
            use_container_width=True,
        )
        st.caption("Retrieves semantically similar chunks, then answers from those chunks.")
    with graph_column:
        st.markdown("**This app: Graph RAG**")
        st.graphviz_chart(
            """
            digraph graph_rag {
              graph [rankdir=LR, bgcolor="transparent"];
              node [shape=box, style="rounded,filled", fontname="Arial", color="#94a3b8"];
              edge [fontname="Arial", fontsize=10, color="#64748b"];
              question [label="Question", fillcolor="#dbeafe"];
              vectors [label="Vector search", fillcolor="#e0e7ff"];
              seeds [label="Matched person /\\nproject records", fillcolor="#fef3c7"];
              joins [label="PostgreSQL joins\\nfollow relationships", fillcolor="#dcfce7"];
              evidence [label="Expanded relational\\nevidence", fillcolor="#d1fae5"];
              answer [label="Grounded LLM answer", fillcolor="#fce7f3"];
              question -> vectors -> seeds -> joins -> evidence -> answer;
            }
            """,
            use_container_width=True,
        )
        st.caption("Starts with vector matches, then follows actual schema relationships for more evidence.")
    st.markdown(
        "**Key difference:** standard RAG stops at retrieved text chunks. Here, vector search finds "
        "person/project records and PostgreSQL follows their skill, assignment, project, and interaction "
        "relationships before answer generation. The graph is the existing relational schema—not a separate graph database."
    )

    st.subheader("Embedding space and relational graph")
    st.write(
        "Each indexed person or project is a point. PCA projects its 384-dimensional embedding "
        "to two dimensions so you can explore semantic neighborhoods. Lines are real assignment "
        "or interaction relationships from PostgreSQL, not inferred from proximity."
    )
    if not os.getenv("DATABASE_URL"):
        st.info("Configure DATABASE_URL and build embeddings to explore the graph.")
    else:
        try:
            graph_data = embedding_graph_data()
            if not graph_data["nodes"]:
                st.info("No current-model embeddings found. Build or refresh embeddings in the next tab.")
            else:
                retrieved_keys = set(
                    st.session_state.get("rag_last_retrieved_keys", [])
                )
                relation_options = ["assignment", "interaction"]
                selected_relations = st.multiselect(
                    "Show relationship types",
                    relation_options,
                    default=relation_options,
                    key="embedding_map_relationships",
                )
                st.caption(
                    "Hover for entity details. Circles are other indexed records; diamonds were "
                    "retrieved for the most recent question. PCA axes are relative coordinates, "
                    "not business measures."
                )
                st.altair_chart(
                    _embedding_map(graph_data, retrieved_keys, selected_relations),
                    use_container_width=True,
                )
                st.caption(
                    f"Showing {len(graph_data['nodes'])} embedded entities and "
                    f"{sum(edge['relation'] in selected_relations for edge in graph_data['edges'])} "
                    "selected relational edges."
                )
        except (psycopg2.Error, ValueError, RuntimeError) as error:
            st.error(f"Could not load the embedding graph: {error}")

    st.subheader("Entity-relationship diagram")
    diagram_path = Path(__file__).with_name("ER_Diagram.PNG")
    if diagram_path.is_file():
        st.image(str(diagram_path), caption="The seven-table capstone relational schema")
    else:
        st.warning("ER_Diagram.PNG was not found next to app.py.")

    st.subheader("What makes this Graph RAG?")
    st.markdown(
        """
        - **Vector retrieval** finds people and projects whose descriptions are semantically relevant to the question.
        - **Relational graph expansion** uses the ERD's foreign-key relationships to fetch connected skills, assignments,
          teammates, and project-scoped interaction metadata. The graph is the existing relational schema, not a separate graph database.
        - **Generation** combines both kinds of evidence. pgvector is the retrieval index; PostgreSQL joins provide explainable relationship paths.
        """
    )
    st.info(
        "The demo embeds derived business records and interaction metadata only. It does not store or embed raw email or chat messages."
    )

with ingest_tab:
    st.header("Build or refresh the vector index")
    st.write(
        "The app reads current person and project records and their skill/assignment relationships, "
        "embeds them locally, then atomically replaces the derived vector rows."
    )
    st.code(
        "Relational tables → SQL-built person/project records → MiniLM embeddings "
        "→ capstone.knowledge_embedding (pgvector)",
        language="text",
    )

    database_configured = bool(os.getenv("DATABASE_URL"))
    if not database_configured:
        st.warning("Configure DATABASE_URL in .env before connecting.")
    else:
        try:
            status = embedding_status()
            left, right = st.columns(2)
            left.metric("Stored knowledge records", status["total"])
            right.metric("Embedding model", MODEL_NAME)
            if status["by_model"]:
                st.caption(
                    "Model counts: "
                    + ", ".join(
                        f"{item['model']}: {item['count']}"
                        for item in status["by_model"]
                    )
                )
        except (psycopg2.Error, ValueError) as error:
            st.error(f"Could not read vector-store status: {error}")

    if st.button(
        "Build / refresh embeddings",
        type="primary",
        disabled=not database_configured,
    ):
        try:
            with st.spinner("Preparing records and generating local embeddings…"):
                count = rebuild_embeddings()
            st.success(f"Stored {count} person/project embeddings in PostgreSQL.")
        except (psycopg2.Error, ValueError, RuntimeError) as error:
            st.error(f"Embedding build failed: {error}")

with ask_tab:
    st.header("Ask a question")
    st.write(
        "Try questions such as “Who has Python experience in Fintech?”, "
        "“Which project involved healthcare compliance?”, or "
        "“Who collaborated on the data platform migration?”"
    )

    with st.form("rag_question_form"):
        question = st.text_input("Business question")
        api_key = st.text_input(
            "Groq API key (optional)",
            value=os.getenv("GROQ_API_KEY", ""),
            type="password",
            help="May be set here for this session or provided as GROQ_API_KEY in .env.",
        )
        model_name = st.text_input(
            "Groq model",
            value=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
        )
        submitted = st.form_submit_button("Retrieve evidence and answer")

    if submitted:
        if not question.strip():
            st.warning("Enter a question to continue.")
        else:
            try:
                with st.spinner("Searching vectors and expanding relational connections…"):
                    matches, graph_context = retrieve(question)
                st.session_state["rag_last_retrieved_keys"] = [
                    (match["source_type"], match["source_id"])
                    for match in matches
                ]
                if not matches:
                    st.info("The vector index is empty. Build embeddings before asking a question.")
                else:
                    evidence = format_evidence(matches, graph_context)
                    st.subheader("Live retrieval graph")
                    st.caption(
                        "This graph reflects the current question: yellow nodes are vector matches; "
                        "green nodes are their relationally expanded records."
                    )
                    st.graphviz_chart(
                        _retrieval_graph(question, matches, graph_context),
                        use_container_width=True,
                    )
                    st.subheader("Retrieved evidence")
                    for match in matches:
                        st.markdown(
                            f"**{match['source_type'].title()} {match['source_id']}** · "
                            f"similarity {match['similarity']:.3f}"
                        )
                        st.write(match["content"])
                    with st.expander("Relational graph expansion"):
                        if graph_context:
                            for item in graph_context:
                                st.write(item)
                        else:
                            st.write("No connected relational records were found.")

                    if api_key.strip():
                        with st.spinner("Generating an evidence-grounded answer with Groq…"):
                            response = Groq(api_key=api_key.strip()).chat.completions.create(
                                model=model_name.strip(),
                                messages=[
                                    {
                                        "role": "system",
                                        "content": (
                                            "Answer the business question using only the supplied evidence. "
                                            "If the evidence is insufficient, say so. Distinguish retrieved facts "
                                            "from inference and cite supporting [person:id] or [project:id] records. "
                                            "Do not invent employee skills, experience, or relationships."
                                        ),
                                    },
                                    {
                                        "role": "user",
                                        "content": f"Question: {question}\n\nEvidence:\n{evidence}",
                                    },
                                ],
                                temperature=0.1,
                                max_tokens=700,
                            )
                        st.subheader("Answer")
                        st.write(response.choices[0].message.content)
                    else:
                        st.info(
                            "Evidence retrieval is complete. Add a Groq API key to generate a natural-language answer."
                        )
                        st.subheader("Evidence-only result")
                        st.write(
                            "The matching records and their linked relational context are shown above. "
                            "No LLM answer was generated because no Groq API key was provided."
                        )
            except (psycopg2.Error, ValueError, RuntimeError) as error:
                st.error(f"Retrieval failed: {error}")
            except APIError as error:
                st.error(f"Groq answer generation failed: {error}")
