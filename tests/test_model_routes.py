from pathlib import Path

import fakeredis
import mlflow
import pytest
from fastapi.testclient import TestClient

from app.core.constants import THRESHOLD
from tests.conftest import csv_file, make_raw_customers


class TestTrain:
    def test_train_without_data_returns_400(self, client: TestClient) -> None:
        response = client.post("/train")

        assert response.status_code == 400
        assert "Not enough data" in response.json()["detail"]

    def test_train_with_too_few_rows_returns_400(self, client: TestClient) -> None:
        client.post("/data/load", files=csv_file(make_raw_customers(n=50)))

        response = client.post("/train")

        assert response.status_code == 400

    def test_train_with_single_class_returns_400(self, client: TestClient) -> None:
        raw = make_raw_customers()
        raw["Churn Value"] = 0
        client.post("/data/load", files=csv_file(raw))

        response = client.post("/train")

        assert response.status_code == 400
        assert "both" in response.json()["detail"]

    def test_train_success(self, loaded_client: TestClient, models_dir: Path) -> None:
        response = loaded_client.post("/train")

        assert response.status_code == 200
        body = response.json()
        assert body["n_rows"] == 300
        assert 0.5 < body["roc_auc"] <= 1.0
        assert (models_dir / f"churn_model_{body['run_id']}.joblib").exists()

    def test_each_training_creates_a_new_versioned_file(
        self, loaded_client: TestClient, models_dir: Path
    ) -> None:
        first = loaded_client.post("/train").json()
        second = loaded_client.post("/train").json()

        assert first["run_id"] != second["run_id"]
        assert len(list(models_dir.glob("churn_model_*.joblib"))) == 2


class TestMlflowTracking:
    def test_training_run_is_logged_to_mlflow(self, loaded_client: TestClient) -> None:
        body = loaded_client.post("/train").json()

        runs = mlflow.search_runs(experiment_names=["churn-model"])

        assert len(runs) == 1
        assert runs.iloc[0]["tags.mlflow.runName"] == body["run_id"]
        assert runs.iloc[0]["metrics.roc_auc"] == pytest.approx(body["roc_auc"])
        assert runs.iloc[0]["params.n_rows"] == "300"

    def test_training_succeeds_when_mlflow_is_unavailable(
        self, loaded_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def broken(*args: object, **kwargs: object) -> None:
            raise ConnectionError("MLflow is down")

        monkeypatch.setattr("app.services.model.mlflow.start_run", broken)

        response = loaded_client.post("/train")

        assert response.status_code == 200


class TestPredict:
    def test_predict_before_training_returns_503(self, client: TestClient, valid_customer: dict) -> None:
        response = client.post("/predict", json=valid_customer)

        assert response.status_code == 503
        assert "not trained" in response.json()["detail"]

    def test_predict_after_training(self, loaded_client: TestClient, valid_customer: dict) -> None:
        loaded_client.post("/train")

        response = loaded_client.post("/predict", json=valid_customer)

        assert response.status_code == 200
        body = response.json()
        assert 0 <= body["churn_probability"] <= 1
        assert body["contact"] == (body["churn_probability"] >= THRESHOLD)

    def test_risky_customer_scores_higher_than_loyal_one(
        self, loaded_client: TestClient, valid_customer: dict
    ) -> None:
        loaded_client.post("/train")
        loyal = {**valid_customer, "contract": "Two year", "tenure_months": 70}

        risky_proba = loaded_client.post("/predict", json=valid_customer).json()["churn_probability"]
        loyal_proba = loaded_client.post("/predict", json=loyal).json()["churn_probability"]

        assert risky_proba > loyal_proba

    def test_model_is_cached_in_redis(
        self, loaded_client: TestClient, valid_customer: dict, fake_redis: fakeredis.FakeRedis
    ) -> None:
        run_id = loaded_client.post("/train").json()["run_id"]

        loaded_client.post("/predict", json=valid_customer)

        assert fake_redis.exists(f"model:{run_id}") == 1

    def test_cached_model_is_used_when_file_disappears(
        self, loaded_client: TestClient, valid_customer: dict, models_dir: Path
    ) -> None:
        loaded_client.post("/train")
        loaded_client.post("/predict", json=valid_customer)
        for file in models_dir.glob("churn_model_*.joblib"):
            file.unlink()

        response = loaded_client.post("/predict", json=valid_customer)

        assert response.status_code == 200

    def test_predict_uses_the_latest_model(
        self, loaded_client: TestClient, valid_customer: dict, fake_redis: fakeredis.FakeRedis
    ) -> None:
        loaded_client.post("/train")
        loaded_client.post("/predict", json=valid_customer)
        second_run = loaded_client.post("/train").json()["run_id"]

        loaded_client.post("/predict", json=valid_customer)

        assert fake_redis.exists(f"model:{second_run}") == 1


class TestPredictValidation:
    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("contract", "Weekly"),
            ("gender", "Other"),
            ("internet_service", "Cable"),
            ("tenure_months", -1),
            ("tenure_months", 121),
            ("monthly_charges", -5.0),
            ("tenure_months", "many"),
        ],
    )
    def test_invalid_value_returns_422(
        self, client: TestClient, valid_customer: dict, field: str, value: object
    ) -> None:
        valid_customer[field] = value

        response = client.post("/predict", json=valid_customer)

        assert response.status_code == 422

    def test_missing_field_returns_422(self, client: TestClient, valid_customer: dict) -> None:
        del valid_customer["contract"]

        response = client.post("/predict", json=valid_customer)

        assert response.status_code == 422

    @pytest.mark.parametrize("tenure", [0, 120])
    def test_boundary_tenure_is_accepted_by_validation(
        self, loaded_client: TestClient, valid_customer: dict, tenure: int
    ) -> None:
        loaded_client.post("/train")
        valid_customer["tenure_months"] = tenure

        response = loaded_client.post("/predict", json=valid_customer)

        assert response.status_code == 200

