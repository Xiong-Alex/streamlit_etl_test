import streamlit as st
import pandas as pd
from sqlalchemy import text
from components.db import get_engine


def render_table_explorer(
    table_name: str,
    session_key: str,
    metric_label: str | None = None,
    allow_truncate: bool = False,
    truncate_sql: str | None = None,
    default_limit: int = 20,
):

    engine = get_engine()

    # ----------------------------------
    # Row Count
    # ----------------------------------
    try:
        row_count = pd.read_sql(
            text(f"SELECT COUNT(*) AS count FROM {table_name};"),
            engine
        )["count"][0]

        label = metric_label or f"Rows in {table_name}"
        st.metric(label, f"{row_count:,}")

    except Exception as e:
        st.error(f"Row count failed: {e}")
        return

    # ----------------------------------
    # Session State
    # ----------------------------------
    query_state_key = f"query_{session_key}"
    editor_key = f"editor_{session_key}"

    default_query = f"SELECT * FROM {table_name} LIMIT {default_limit};"

    if query_state_key not in st.session_state:
        st.session_state[query_state_key] = default_query

    # ----------------------------------
    # Data Preview
    # ----------------------------------
    try:
        df = pd.read_sql(
            text(st.session_state[query_state_key]),
            engine
        )
        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.warning(f"Preview failed: {e}")

    # ----------------------------------
    # Query Editor
    # ----------------------------------
    edited_query = st.text_area(
        label="",
        value=st.session_state[query_state_key],
        height=150,
        key=editor_key,
    )

    col1, col2 = st.columns(2)

    # ----------------------------------
    # Run Query
    # ----------------------------------
    with col1:
        if st.button("Run Query", key=f"run_{session_key}", use_container_width=True):
            st.session_state[query_state_key] = edited_query
            st.rerun()

    # ----------------------------------
    # Truncate Table
    # ----------------------------------
    with col2:
        if allow_truncate and truncate_sql:
            if st.button(
                "Truncate Table",
                key=f"truncate_{session_key}",
                use_container_width=True
            ):
                try:
                    with engine.begin() as conn:
                        conn.execute(text(truncate_sql))
                    st.success(f"{table_name} truncated.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Truncate failed: {e}")
