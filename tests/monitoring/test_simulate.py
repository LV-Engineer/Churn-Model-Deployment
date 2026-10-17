import pandas as pd
import pytest

from app.monitoring.simulate import apply_drift


class TestApplyDrift:
    def test_monthly_charges_grow_by_thirty_percent(self, exported_customers: pd.DataFrame) -> None:
        drifted = apply_drift(exported_customers)

        ratio = drifted["monthly_charges"].mean() / exported_customers["monthly_charges"].mean()
        assert ratio == pytest.approx(1.3, rel=0.01)

    def test_tenure_gets_shorter(self, exported_customers: pd.DataFrame) -> None:
        drifted = apply_drift(exported_customers)

        assert drifted["tenure_months"].mean() < exported_customers["tenure_months"].mean()
        assert (drifted["tenure_months"] >= 0).all()

    def test_more_month_to_month_contracts(self, exported_customers: pd.DataFrame) -> None:
        drifted = apply_drift(exported_customers)

        def share(frame: pd.DataFrame) -> float:
            return float((frame["contract"] == "Month-to-month").mean())

        assert share(drifted) > share(exported_customers)

    def test_more_fiber_optic(self, exported_customers: pd.DataFrame) -> None:
        drifted = apply_drift(exported_customers)

        def share(frame: pd.DataFrame) -> float:
            return float((frame["internet_service"] == "Fiber optic").mean())

        assert share(drifted) > share(exported_customers)

    def test_other_columns_are_untouched(self, exported_customers: pd.DataFrame) -> None:
        drifted = apply_drift(exported_customers)

        for column in ("gender", "partner", "payment_method", "churn_value"):
            pd.testing.assert_series_equal(drifted[column], exported_customers[column])

    def test_customer_ids_are_marked(self, exported_customers: pd.DataFrame) -> None:
        drifted = apply_drift(exported_customers)

        assert drifted["customer_id"].str.startswith("DRIFT-").all()

    def test_zero_strength_changes_no_features(self, exported_customers: pd.DataFrame) -> None:
        drifted = apply_drift(exported_customers, strength=0)

        features = [c for c in exported_customers.columns if c != "customer_id"]
        pd.testing.assert_frame_equal(drifted[features], exported_customers[features])

    def test_same_seed_gives_same_result(self, exported_customers: pd.DataFrame) -> None:
        first = apply_drift(exported_customers, seed=1)
        second = apply_drift(exported_customers, seed=1)

        pd.testing.assert_frame_equal(first, second)

    def test_does_not_modify_input(self, exported_customers: pd.DataFrame) -> None:
        before = exported_customers.copy()

        apply_drift(exported_customers)

        pd.testing.assert_frame_equal(exported_customers, before)
