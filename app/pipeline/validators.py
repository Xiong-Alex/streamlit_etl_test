# ----------------------------------
# Imports
# ----------------------------------
from sqlalchemy import text


# ==================================
# CORE UTILITIES
# ==================================

def table_exists(engine, table_name: str) -> bool:
    schema, table = table_name.split(".")

    query = text("""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = :schema
              AND table_name = :table
        )
    """)

    with engine.begin() as conn:
        return conn.execute(
            query,
            {"schema": schema, "table": table}
        ).scalar()


def table_has_rows(engine, table_name: str) -> bool:
    query = text(f"SELECT 1 FROM {table_name} LIMIT 1")

    with engine.begin() as conn:
        return conn.execute(query).first() is not None


def table_columns(engine, table_name: str) -> set:
    """
    Returns set of column names for given table.
    """

    schema, table = table_name.split(".")

    query = text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = :schema
          AND table_name = :table
    """)

    with engine.begin() as conn:
        result = conn.execute(
            query,
            {"schema": schema, "table": table}
        ).fetchall()

    return {row[0] for row in result}


# ==================================
# STRICT VALIDATOR
# ==================================

def validate_table(
    engine,
    table_name: str,
    not_empty: bool = False,
    required_columns: list[str] | None = None,
) -> bool:
    """
    Strict table validator.

    Always enforces table existence.
    Optionally enforces non-empty and required columns.

    Returns:
        True if validation passes.
        False only when not_empty=True and table is empty.

    Raises:
        RuntimeError if table does not exist
        RuntimeError if required columns are missing
    """

    # -----------------------------
    # Existence (ALWAYS REQUIRED)
    # -----------------------------
    if not table_exists(engine, table_name):
        raise RuntimeError(f"Required table does not exist: {table_name}")

    # -----------------------------
    # Column validation
    # -----------------------------
    if required_columns:
        existing_columns = table_columns(engine, table_name)
        missing = set(required_columns) - existing_columns

        if missing:
            raise RuntimeError(
                f"{table_name} missing required columns: {missing}"
            )

    # -----------------------------
    # Non-empty validation
    # -----------------------------
    if not_empty:
        if not table_has_rows(engine, table_name):
            return False

    return True
