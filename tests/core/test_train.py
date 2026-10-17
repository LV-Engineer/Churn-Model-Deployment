import pandas as pd

from app.core.constants import TARGET
from app.core.data import clean
from app.core.train import fit_model


class TestFitModel:
    def test_returns_pipeline_and_auc_in_valid_range(self, raw_customers: pd.DataFrame) -> None:
        pipeline, auc = fit_model(clean(raw_customers))

        assert 0.5 < auc <= 1.0
        assert hasattr(pipeline, "predict_proba")

    def test_pipeline_outputs_probabilities(self, raw_customers: pd.DataFrame) -> None:
        df = clean(raw_customers)
        pipeline, _ = fit_model(df)

        proba = pipeline.predict_proba(df.drop(columns=[TARGET]))[:, 1]

        assert ((proba >= 0) & (proba <= 1)).all()

    def test_is_reproducible(self, raw_customers: pd.DataFrame) -> None:
        df = clean(raw_customers)

        _, first = fit_model(df)
        _, second = fit_model(df)

        assert first == second
