from olist_agent.tools import call_tool, describe_table, list_tables


def test_list_tables_includes_fct_orders():
    assert '"03_data_warehouse".fct_orders' in list_tables()


def test_describe_table_lists_columns_with_types():
    result = describe_table("03_data_warehouse", "fct_orders")
    assert "purchased_at (timestamp without time zone)" in result


def test_describe_table_reports_unknown_table():
    result = describe_table("03_data_warehouse", "no_such_table")
    assert "Table not found" in result


def test_call_tool_runs_the_named_tool():
    assert call_tool("list_tables", "{}") == list_tables()


def test_call_tool_passes_arguments():
    result = call_tool("describe_table", '{"schema": "03_data_warehouse", "table": "fct_orders"}')
    assert "order_id" in result


def test_call_tool_reports_unknown_tool():
    assert call_tool("drop_everything", "{}") == "Unknown tool: drop_everything"


def test_call_tool_reports_bad_arguments():
    assert call_tool("run_sql", "not json").startswith("Invalid arguments")
