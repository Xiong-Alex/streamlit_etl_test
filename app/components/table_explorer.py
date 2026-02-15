import streamlit as st
import pandas as pd
from sqlalchemy import text
from components.db import get_engine


def render_table_explorer(
    table_name: str,
    session_key: str,
    metric_label: str | None = None,
    allow_truncate: bool = False,
    default_limit: int = 10,
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
    query_key = f"query_{session_key}"
    editor_key = f"editor_{session_key}"

    if query_key not in st.session_state:
        st.session_state[query_key] = (
            f"SELECT * FROM {table_name} LIMIT {default_limit};"
        )

    # ----------------------------------
    # AUTO PREVIEW (FIRST)
    # ----------------------------------
    try:
        with engine.begin() as conn:
            result = conn.execute(text(st.session_state[query_key]))

            if result.returns_rows:
                df = pd.DataFrame(
                    result.fetchall(),
                    columns=result.keys()
                )
                st.dataframe(df, width="stretch")
            else:
                st.success(
                    f"Query executed successfully. "
                    f"{result.rowcount} rows affected."
                )

    except Exception as e:
        st.warning(f"Query failed: {e}")


    # ----------------------------------
    # QUERY EDITOR (AFTER PREVIEW)
    # ----------------------------------
    edited_query = st.text_area(
        "SQL Query",
        value=st.session_state[query_key],
        height=150,
        key=editor_key,
        label_visibility="collapsed",
    )

    col1, col2 = st.columns(2)

    # ----------------------------------
    # RUN BUTTON
    # ----------------------------------
    with col1:
        if st.button("Run Query", key=f"run_{session_key}", width="stretch"):
            st.session_state[query_key] = edited_query

    # ----------------------------------
    # TRUNCATE BUTTON
    # ----------------------------------
    with col2:
        if allow_truncate:
            if st.button(
                "Truncate Table",
                key=f"truncate_{session_key}",
                use_container_width=True
            ):
                try:
                    with engine.begin() as conn:
                        conn.execute(text(f"TRUNCATE TABLE {table_name};"))

                    st.success(f"{table_name} truncated.")
                    st.rerun()

                except Exception as e:
                    st.error(f"Truncate failed: {e}")

