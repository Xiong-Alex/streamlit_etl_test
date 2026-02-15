# ----------------------------------
# Imports
# ----------------------------------
from sqlalchemy import text


# ==================================
# CORE UTILITIES
# ==================================

from sqlalchemy import text


def table_exists(engine, table_name: str) -> bool:
    """
    Checks whether a database object exists.

    Supports:
        - Tables
        - Regular views
        - Materialized views

    Args:
        engine: SQLAlchemy engine instance
        table_name: Fully-qualified name in format "schema.object"

    Returns:
        True if object exists, False otherwise.
    """

    # ----------------------------------------
    # Split "schema.table" into components
    # ----------------------------------------
    schema, table = table_name.split(".")

    # ----------------------------------------
    # Query explanation:
    #
    # 1) information_schema.tables
    #    Covers:
    #       - Tables
    #       - Regular views
    #
    # 2) pg_matviews
    #    Covers:
    #       - Materialized views
    #
    # We use OR EXISTS so either object type
    # returns True.
    # ----------------------------------------
    query = text("""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = :schema
              AND table_name = :table
        )
        OR EXISTS (
            SELECT 1
            FROM pg_matviews
            WHERE schemaname = :schema
              AND matviewname = :table
        )
    """)

    # ----------------------------------------
    # Execute safely inside a transaction block
    # ----------------------------------------
    with engine.begin() as conn:
        return conn.execute(
            query,
            {"schema": schema, "table": table}
        ).scalar()



def table_has_rows(engine, table_name: str) -> bool:
    """
    Checks whether a table contains at least one row.

    Used for optional non-empty validation.
    """

    query = text(f"SELECT 1 FROM {table_name} LIMIT 1")

    with engine.begin() as conn:
        return conn.execute(query).first() is not None


def table_columns(engine, table_name: str) -> set:
    """
    Returns a set of column names for the given table.

    Args:
        engine: SQLAlchemy engine
        table_name: "schema.table"

    Returns:
        Set of column names.
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

    Responsibilities:
    - ALWAYS enforce table existence.
    - Optionally enforce required columns.
    - Optionally enforce non-empty condition.

    This function does NOT:
    - Create tables
    - Modify schema
    - Perform side effects

    That responsibility belongs to the DB layer.

    Args:
        engine: SQLAlchemy engine
        table_name: "schema.table"
        not_empty: If True, table must contain at least one row.
        required_columns: List of column names that must exist.

    Returns:
        True if validation passes.
        False ONLY when not_empty=True and table exists but has no rows.

    Raises:
        RuntimeError:
            - If table does not exist
            - If required columns are missing
    """

    # ------------------------------------------------
    # 1️⃣ Existence Check (ALWAYS REQUIRED)
    # ------------------------------------------------
    if not table_exists(engine, table_name):
        raise RuntimeError(
            f"Required table does not exist: {table_name}"
        )

    # ------------------------------------------------
    # 2️⃣ Column Validation (Optional)
    # ------------------------------------------------
    if required_columns:
        existing_columns = table_columns(engine, table_name)
        missing = set(required_columns) - existing_columns

        if missing:
            raise RuntimeError(
                f"{table_name} missing required columns: {missing}"
            )

    # ------------------------------------------------
    # 3️⃣ Non-Empty Validation (Optional)
    # ------------------------------------------------
    if not_empty:
        if not table_has_rows(engine, table_name):
            # We return False instead of raising because
            # emptiness is often used for pipeline flow control
            return False

    # ------------------------------------------------
    # Validation Passed
    # ------------------------------------------------
    return True
