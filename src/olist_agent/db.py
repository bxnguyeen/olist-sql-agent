import psycopg
from dotenv import load_dotenv

load_dotenv()

STATEMENT_TIMEOUT_MS = 10_000

def run_query(
        sql: str, params: list | None = None, max_rows: int | None = None
) -> tuple[list[str], list[tuple]]:
    """Run a read-only SQL query, return (column, rows)."""
    with psycopg.connect(options=f"-c statement_timeout={STATEMENT_TIMEOUT_MS}") as conn:
        conn.read_only = True
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if cur.description is None:
                return [], []
            columns = [col.name for col in cur.description]
            rows = cur.fetchmany(max_rows) if max_rows else cur.fetchall()
            return columns, rows