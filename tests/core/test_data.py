import pandas as pd
import pytest

from app.core.constants import DROP_COLS
from app.core.data import clean


class TestClean:
    def test_drops_leaky_and_useless_columns(self, raw_customers: pd.DataFrame) -> None:
        cleaned = clean(raw_customers)

        for column in DROP_COLS:
            assert column not in cleaned.columns

    def test_uses_customer_id_as_index(self, raw_customers: pd.DataFrame) -> None:
        cleaned = clean(raw_customers)

        assert cleaned.index.name == "CustomerID"
        assert cleaned.index[0] == "CUST-00000"

    def test_blank_total_charges_become_zero(self, raw_customers: pd.DataFrame) -> None:
        cleaned = clean(raw_customers)

        assert cleaned["Total Charges"].iloc[0] == 0
        assert pd.api.types.is_numeric_dtype(cleaned["Total Charges"])

    def test_keeps_target(self, raw_customers: pd.DataFrame) -> None:
        cleaned = clean(raw_customers)

        assert set(cleaned["Churn Value"].unique()) == {0, 1}

    def test_does_not_modify_input(self, raw_customers: pd.DataFrame) -> None:
        before = raw_customers.copy()

        clean(raw_customers)

        pd.testing.assert_frame_equal(raw_customers, before)

    def test_missing_column_raises_key_error(self, raw_customers: pd.DataFrame) -> None:
        broken = raw_customers.drop(columns=["Contract"])

        with pytest.raises(KeyError):
            clean(broken)

    def test_numeric_total_charges_are_accepted(self, raw_customers: pd.DataFrame) -> None:
        # e.g. a parquet file where Total Charges is already a number
        raw_customers["Total Charges"] = pd.to_numeric(raw_customers["Total Charges"], errors="coerce").fillna(0)

        cleaned = clean(raw_customers)

        assert pd.api.types.is_numeric_dtype(cleaned["Total Charges"])
