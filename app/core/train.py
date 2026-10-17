import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app.core.constants import SEED, TARGET
from app.core.features import build_preprocessor

def fit_model(df: pd.DataFrame) -> tuple[Pipeline, float]:
    """Fit the pipeline on cleaned data, return it with the test ROC-AUC."""
    X = df.drop(columns=[TARGET])
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=SEED
    )

    model = Pipeline([
        ("prep", build_preprocessor()),
        ("clf", LogisticRegression(max_iter=1000)),
    ])
    model.fit(X_train, y_train)

    auc = float(roc_auc_score(y_test, model.predict_proba(X_test)[:, 1]))
    return model, auc