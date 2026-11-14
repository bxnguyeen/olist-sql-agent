import psycopg
from olist_agent.db import run_query

ALLOWED_SCHEMAS = ["03_data_warehouse", "02_stg"]

def list_tables() -> str:
    """List the tables the agent is allowed to query, one per line."""
    _, rows = run_query(
        """
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema = ANY(%s)
        ORDER BY table_schema, table_name
        """,
        [ALLOWED_SCHEMAS],
    )
    return "\n".join(f'"{schema}".{table}' for schema, table in rows)


def describe_table(schema: str, table: str) -> str:
    """Return the columns of a table with their data types, one per line."""
    _, rows = run_query(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = %s
            AND table_name = %s
        ORDER BY ordinal_position
        """,
        [schema, table],
    )
    if not rows:
        return "Table not found. Call list_tables to see the available tables."
    return "\n".join(f"{name} ({dtype})" for name, dtype in rows)


MAX_ROWS = 50

def run_sql(query: str) -> str:
    """Run a read-only SQL query and return the result (or the error) as text."""
    try:
        columns, rows = run_query(query, max_rows=MAX_ROWS + 1)
    except psycopg.Error as error:
        return f"SQL error: {error}"

    lines = [" | ".join(columns)]
    lines += [" | ".join(str(value) for value in row) for row in rows[:MAX_ROWS]]
    if len(rows) > MAX_ROWS:
        lines.append(f"(only the first {MAX_ROWS} rows are shown; aggregate or add LIMIT)")
    if not rows:
        lines.append("(0 rows)")
    return "\n".join(lines)