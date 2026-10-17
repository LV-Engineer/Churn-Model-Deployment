from fastapi.testclient import TestClient


def test_custom_metrics_are_exposed(loaded_client: TestClient, valid_customer: dict) -> None:
    loaded_client.post("/train")
    loaded_client.post("/predict", json=valid_customer)

    body = loaded_client.get("/metrics").text

    assert "http_requests_total" in body
    assert "churn_predictions_total" in body
    assert "churn_predicted_probability_bucket" in body
    assert "churn_model_roc_auc" in body