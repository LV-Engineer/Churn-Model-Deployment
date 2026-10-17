import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def apply_drift(df: pd.DataFrame, strength: float = 1.0, seed: int = 42) -> pd.DataFrame:
    """Return a copy of exported customer data with a deliberate shift in the distributions.

    At strength 1: monthly charges +30%, tenure -40%, 30% of customers moved to a
    month-to-month contract, 20% moved to fiber optic. Strength 0 changes nothing.
    """
    strength = max(strength, 0.0)
    rng = np.random.default_rng(seed)
    drifted = df.copy()

    drifted["customer_id"] = "DRIFT-" + drifted["customer_id"].astype(str)
    drifted["monthly_charges"] = (drifted["monthly_charges"] * (1 + 0.3 * strength)).round(2)
    drifted["tenure_months"] = (
        (drifted["tenure_months"] * (1 - 0.4 * strength)).round().clip(lower=0).astype(int)
    )
    _set_share(drifted, "contract", "Month-to-month", 0.3 * strength, rng)
    _set_share(drifted, "internet_service", "Fiber optic", 0.2 * strength, rng)

    return drifted


def _set_share(
    df: pd.DataFrame, column: str, value: str, share: float, rng: np.random.Generator
) -> None:
    """Overwrite `column` with `value` for a random share of the rows."""
    mask = rng.random(len(df)) < min(share, 1.0)
    df.loc[mask, column] = value


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a drifted copy of exported customer data")
    parser.add_argument("input", type=Path, help="CSV exported with GET /data/export")
    parser.add_argument("output", type=Path, help="where to write the drifted CSV")
    parser.add_argument("--strength", type=float, default=1.0, help="size of the shift, 1.0 is the default")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    drifted = apply_drift(pd.read_csv(args.input), args.strength, args.seed)
    drifted.to_csv(args.output, index=False)
    print(f"Wrote {len(drifted)} rows to {args.output}")


if __name__ == "__main__":
    main()
