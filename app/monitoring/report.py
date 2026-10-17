import argparse
import sys
from pathlib import Path

import pandas as pd

from app.monitoring.drift import DRIFT_SHARE_THRESHOLD, detect_drift, drift_report_html


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare new customer data with the reference data")
    parser.add_argument("reference", type=Path, help="CSV exported with GET /data/export")
    parser.add_argument("current", type=Path, help="CSV with new data in the same format")
    parser.add_argument("--html", type=Path, help="where to save the Evidently HTML report")
    args = parser.parse_args()

    reference = pd.read_csv(args.reference)
    current = pd.read_csv(args.current)

    result = detect_drift(reference, current)
    print(f"Drifted columns: {len(result.drifted_features)} ({result.drift_share:.0%}, alert at {DRIFT_SHARE_THRESHOLD:.0%})")
    print(f"Features: {', '.join(result.drifted_features) or 'none'}")
    print(f"ALERT: {'yes' if result.alert else 'no'}")

    if args.html:
        args.html.write_text(drift_report_html(reference, current), encoding="utf-8")
        print(f"Report saved to {args.html}")

    sys.exit(1 if result.alert else 0)


if __name__ == "__main__":
    main()
