import pandas as pd
import pytest

from app.monitoring.drift import DRIFT_SHARE_THRESHOLD, KEY_FEATURES, detect_drift, drift_report_html
from app.monitoring.simulate import apply_drift


class TestDetectDrift:
    def test_identical_data_has_no_drift(self, exported_customers: pd.DataFrame) -> None:
        result = detect_drift(exported_customers, exported_customers.copy())

        assert result.drifted_features == []
        assert result.drift_share == 0
        assert result.alert is False

    def test_simulated_shift_is_detected(self, exported_customers: pd.DataFrame) -> None:
        drifted = apply_drift(exported_customers)

        result = detect_drift(exported_customers, drifted)

        assert result.alert is True
        assert {"monthly_charges", "tenure_months"} <= set(result.drifted_features)

    def test_untouched_columns_do_not_drift(self, exported_customers: pd.DataFrame) -> None:
        result = detect_drift(exported_customers, apply_drift(exported_customers))

        assert "gender" not in result.drifted_features
        assert "payment_method" not in result.drifted_features

    def test_alert_when_a_key_feature_drifts(self, exported_customers: pd.DataFrame) -> None:
        current = exported_customers.copy()
        current["monthly_charges"] = current["monthly_charges"] * 2

        result = detect_drift(exported_customers, current)

        assert result.drifted_features == ["monthly_charges"]
        assert result.drift_share < DRIFT_SHARE_THRESHOLD
        assert "monthly_charges" in KEY_FEATURES
        assert result.alert is True

    def test_no_alert_when_only_a_minor_feature_drifts(self, exported_customers: pd.DataFrame) -> None:
        current = exported_customers.copy()
        current["streaming_tv"] = "Yes"

        result = detect_drift(exported_customers, current)

        assert "streaming_tv" in result.drifted_features
        assert result.alert is False

    def test_missing_column_raises(self, exported_customers: pd.DataFrame) -> None:
        with pytest.raises(ValueError, match="missing columns"):
            detect_drift(exported_customers, exported_customers.drop(columns=["contract"]))

    def test_empty_data_raises(self, exported_customers: pd.DataFrame) -> None:
        with pytest.raises(ValueError, match="empty"):
            detect_drift(exported_customers, exported_customers.iloc[0:0])


def test_html_report_is_generated(exported_customers: pd.DataFrame) -> None:
    html = drift_report_html(exported_customers, apply_drift(exported_customers))

    assert "<html" in html.lower()
