import io

import pandas as pd
from fastapi.testclient import TestClient

from tests.conftest import csv_file, parquet_file


class TestLoad:
    def test_load_csv(self, client: TestClient, raw_customers: pd.DataFrame) -> None:
        response = client.post("/data/load", files=csv_file(raw_customers))

        assert response.status_code == 200
        assert response.json() == {"rows_added": 300, "rows_skipped": 0}

    def test_load_parquet(self, client: TestClient, raw_customers: pd.DataFrame) -> None:
        response = client.post("/data/load", files=parquet_file(raw_customers))

        assert response.status_code == 200
        assert response.json()["rows_added"] == 300

    def test_loading_same_file_twice_skips_duplicates(
        self, client: TestClient, raw_customers: pd.DataFrame
    ) -> None:
        client.post("/data/load", files=csv_file(raw_customers))

        response = client.post("/data/load", files=csv_file(raw_customers))

        assert response.json() == {"rows_added": 0, "rows_skipped": 300}

    def test_duplicates_inside_one_file_are_collapsed(
        self, client: TestClient, raw_customers: pd.DataFrame
    ) -> None:
        doubled = pd.concat([raw_customers, raw_customers])

        response = client.post("/data/load", files=csv_file(doubled))

        assert response.json()["rows_added"] == 300

    def test_unsupported_extension_returns_400(self, client: TestClient) -> None:
        files = {"file": ("customers.txt", b"hello", "text/plain")}

        response = client.post("/data/load", files=files)

        assert response.status_code == 400
        assert "Unsupported" in response.json()["detail"]

    def test_missing_columns_return_400(self, client: TestClient, raw_customers: pd.DataFrame) -> None:
        broken = raw_customers.drop(columns=["Contract"])

        response = client.post("/data/load", files=csv_file(broken))

        assert response.status_code == 400

    def test_missing_file_returns_422(self, client: TestClient) -> None:
        response = client.post("/data/load")

        assert response.status_code == 422


class TestExport:
    def test_export_csv_contains_all_rows(self, loaded_client: TestClient) -> None:
        response = loaded_client.get("/data/export", params={"format": "csv"})

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        assert "customers.csv" in response.headers["content-disposition"]
        frame = pd.read_csv(io.BytesIO(response.content))
        assert len(frame) == 300
        assert {"customer_id", "tenure_months", "churn_value"} <= set(frame.columns)

    def test_export_parquet_contains_all_rows(self, loaded_client: TestClient) -> None:
        response = loaded_client.get("/data/export", params={"format": "parquet"})

        assert response.status_code == 200
        frame = pd.read_parquet(io.BytesIO(response.content))
        assert len(frame) == 300

    def test_export_defaults_to_csv(self, loaded_client: TestClient) -> None:
        response = loaded_client.get("/data/export")

        assert response.headers["content-type"].startswith("text/csv")

    def test_export_empty_database_has_only_header(self, client: TestClient) -> None:
        response = client.get("/data/export")

        frame = pd.read_csv(io.BytesIO(response.content))
        assert frame.empty
        assert "customer_id" in frame.columns

    def test_export_unknown_format_returns_422(self, client: TestClient) -> None:
        response = client.get("/data/export", params={"format": "xlsx"})

        assert response.status_code == 422


class TestClear:
    def test_clear_removes_all_rows(self, loaded_client: TestClient) -> None:
        response = loaded_client.delete("/data/clear")

        assert response.status_code == 200
        assert response.json() == {"rows_deleted": 300}
        exported = pd.read_csv(io.BytesIO(loaded_client.get("/data/export").content))
        assert exported.empty

    def test_clear_empty_database_deletes_nothing(self, client: TestClient) -> None:
        response = client.delete("/data/clear")

        assert response.json() == {"rows_deleted": 0}
