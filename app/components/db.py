from sqlalchemy import create_engine
import streamlit as st

@st.cache_resource
def get_engine():
    return create_engine(
        "postgresql+psycopg2://postgres:postgres@postgres:5432/etl_db"
    )

#setup w/.env later