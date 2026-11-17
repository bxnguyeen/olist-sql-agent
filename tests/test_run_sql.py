from olist_agent.tools import MAX_ROWS, run_sql
import pytest
pytestmark = pytest.mark.db


def test_run_sql_returns_header_and_rows():
    result = run_sql('SELECT count(*) AS orders FROM "03_data_warehouse".fct_orders')
    assert result == "orders\n99441"


def test_run_sql_returns_error_as_text():
    result = run_sql("SELECT * FROM no_such_table")
    assert result.startswith("SQL error:")
    assert "no_such_table" in result


def test_run_sql_rejects_writes():
    result = run_sql('CREATE TABLE "02_stg".should_fail (id int)')
    assert "read-only transaction" in result


def test_run_sql_truncates_long_results():
    result = run_sql('SELECT order_id FROM "03_data_warehouse".fct_orders')
    assert len(result.splitlines()) == MAX_ROWS + 2  # header + rows + notice


def test_run_sql_reports_empty_result():
    result = run_sql("SELECT 1 AS x WHERE false")
    assert result == "x\n(0 rows)"