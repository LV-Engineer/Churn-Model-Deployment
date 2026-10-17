from dataclasses import dataclass
from typing import Any

import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset

from app.core.constants import FEATURE_TO_DB, TARGET

# Columns compared between the reference and the new data (database names, without the target).
MONITORED_COLUMNS = [column for raw, column in FEATURE_TO_DB.items() if raw != TARGET]

# Alert rule: raise an alert when at least this share of the columns drifted ...
DRIFT_SHARE_THRESHOLD = 0.3
# ... or when any of these columns drifted (the strongest churn drivers from Project 1).
KEY_FEATURES = ("tenure_months", "monthly_charges", "contract")

_COLUMN_TEST_PREFIX = "Value Drift for column "


@dataclass(frozen=True)
class DriftResult:
    drift_share: float
    drifted_features: list[str]
    alert: bool


def detect_drift(reference: pd.DataFrame, current: pd.DataFrame) -> DriftResult:
    """Compare new data with the reference data and apply the alert rule."""
    snapshot = _run_report(reference, current, include_tests=True)

    drifted = [
        test["name"].removeprefix(_COLUMN_TEST_PREFIX)
        for test in snapshot.dict()["tests"]
        if test["name"].startswith(_COLUMN_TEST_PREFIX) and test["status"].value == "FAIL"
    ]
    drifted.sort(key=MONITORED_COLUMNS.index)

    share = len(drifted) / len(MONITORED_COLUMNS)
    alert = share >= DRIFT_SHARE_THRESHOLD or any(feature in KEY_FEATURES for feature in drifted)
    return DriftResult(drift_share=share, drifted_features=drifted, alert=alert)


def drift_report_html(reference: pd.DataFrame, current: pd.DataFrame) -> str:
    """Full Evidently data drift report as a standalone HTML page."""
    return str(_run_report(reference, current, include_tests=False).get_html_str(as_iframe=False))


def _run_report(reference: pd.DataFrame, current: pd.DataFrame, include_tests: bool) -> Any:
    _check(reference, "reference")
    _check(current, "current")
    report = Report([DataDriftPreset()], include_tests=include_tests)
    return report.run(current[MONITORED_COLUMNS], reference[MONITORED_COLUMNS])


def _check(df: pd.DataFrame, name: str) -> None:
    missing = [column for column in MONITORED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"The {name} data is missing columns: {', '.join(missing)}")
    if df.empty:
        raise ValueError(f"The {name} data is empty")
