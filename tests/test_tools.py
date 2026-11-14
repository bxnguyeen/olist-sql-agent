from olist_agent.tools import describe_table, list_tables


def test_list_tables_includes_fct_orders():
    assert '"03_data_warehouse".fct_orders' in list_tables()


def test_describe_table_lists_columns_with_types():
    result = describe_table("03_data_warehouse", "fct_orders")
    assert "purchased_at (timestamp without time zone)" in result


def test_describe_table_reports_unknown_table():
    result = describe_table("03_data_warehouse", "no_such_table")
    assert "Table not found" in result
