import pandas as pd
from fastapi.testclient import TestClient

from app.monitoring.simulate import apply_drift


def csv_upload(df: pd.DataFrame) -> dict:
    return {"file": ("new_data.csv", df.to_csv(index=False).encode(), "text/csv")}


class TestDriftCheck:
    def test_no_reference_data_returns_400(self, client: TestClient, exported_customers: pd.DataFrame) -> None:
        response = client.post("/monitoring/drift", files=csv_upload(exported_customers))

        assert response.status_code == 400
        assert "No reference data" in response.json()["detail"]

    def test_unchanged_data_has_no_alert(
        self, loaded_client: TestClient, exported_customers: pd.DataFrame
    ) -> None:
        response = loaded_client.post("/monitoring/drift", files=csv_upload(exported_customers))

        assert response.status_code == 200
        assert response.json() == {"drift_share": 0, "drifted_features": [], "alert": False}

    def test_shifted_data_raises_an_alert(
        self, loaded_client: TestClient, exported_customers: pd.DataFrame
    ) -> None:
        shifted = apply_drift(exported_customers)

        response = loaded_client.post("/monitoring/drift", files=csv_upload(shifted))

        assert response.status_code == 200
        body = response.json()
        assert body["alert"] is True
        assert "monthly_charges" in body["drifted_features"]
        assert 0 < body["drift_share"] <= 1

    def test_missing_columns_return_400(
        self, loaded_client: TestClient, exported_customers: pd.DataFrame
    ) -> None:
        broken = exported_customers.drop(columns=["contract"])

        response = loaded_client.post("/monitoring/drift", files=csv_upload(broken))

        assert response.status_code == 400
        assert "contract" in response.json()["detail"]

    def test_empty_file_returns_400(self, loaded_client: TestClient) -> None:
        files = {"file": ("new_data.csv", b"", "text/csv")}

        response = loaded_client.post("/monitoring/drift", files=files)

        assert response.status_code == 400

    def test_missing_file_returns_422(self, client: TestClient) -> None:
        response = client.post("/monitoring/drift")

        assert response.status_code == 422


class TestDriftReport:
    def test_report_is_returned_as_a_downloadable_html_file(
        self, loaded_client: TestClient, exported_customers: pd.DataFrame
    ) -> None:
        shifted = apply_drift(exported_customers)

        response = loaded_client.post("/monitoring/drift/report", files=csv_upload(shifted))

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert "attachment" in response.headers["content-disposition"]
        assert "drift_report.html" in response.headers["content-disposition"]
        assert "<html" in response.text.lower()

    def test_report_without_reference_data_returns_400(
        self, client: TestClient, exported_customers: pd.DataFrame
    ) -> None:
        response = client.post("/monitoring/drift/report", files=csv_upload(exported_customers))

        assert response.status_code == 400

    def test_report_with_missing_columns_returns_400(
        self, loaded_client: TestClient, exported_customers: pd.DataFrame
    ) -> None:
        broken = exported_customers.drop(columns=["tenure_months"])

        response = loaded_client.post("/monitoring/drift/report", files=csv_upload(broken))

        assert response.status_code == 400
