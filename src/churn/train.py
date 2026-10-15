import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from churn.config import MODEL_PATH, RAW_PATH, SEED, TARGET
from churn.data import clean, load_raw
from churn.features import build_preprocessor

def train() -> float:
    """Train the model, save it to MODEL_PATH, return test ROC-AUC."""
    df = clean(load_raw(RAW_PATH))
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

    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    return float(roc_auc_score(y_test, model.predict_proba(X_test)[:, 1]))