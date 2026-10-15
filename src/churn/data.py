import pandas as pd
from pathlib import Path

from churn.config import DROP_COLS, CAT_COLS

def load_raw(path: Path) -> pd.DataFrame:
    """Read the raw CSV as is, without any cleaning."""
    return pd.read_csv(path)

def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Drop useless/leaky columns, fix dtypes. Returns a new DataFrame."""
    df = df.drop(columns=DROP_COLS).set_index("CustomerID")

    df[CAT_COLS] = df[CAT_COLS].astype("category")

    df['Total Charges'] = pd.to_numeric(df['Total Charges'].str.strip(), errors='coerce').fillna(0)
    assert df["Total Charges"].ge(0).all()

    return df