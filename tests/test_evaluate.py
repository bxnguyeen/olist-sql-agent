from decimal import Decimal

from olist_agent.evaluate import results_match


def test_identical_results_match():
    assert results_match([(6534,)], [(6534,)])


def test_different_values_do_not_match():
    assert not results_match([("SP", Decimal("2975757.23"))], [("SP", Decimal("3626074.64"))])


def test_number_types_and_tiny_differences_are_ignored():
    assert results_match([(Decimal("2975757.23"),)], [(2975757.2300001,)])


def test_extra_columns_and_column_order_are_ignored():
    assert results_match([("SP", 10)], [(10, "SP", "extra")])


def test_row_order_is_ignored():
    assert results_match([("SP", 1), ("RJ", 2)], [("RJ", 2), ("SP", 1)])


def test_different_row_counts_do_not_match():
    assert not results_match([("SP", 1)], [("SP", 1), ("RJ", 2)])
