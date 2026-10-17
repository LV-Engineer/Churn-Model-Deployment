from pathlib import Path

import pandas as pd
import pytest

from app.monitoring import report, simulate


def test_simulate_script_writes_a_drifted_csv(
    exported_customers: pd.DataFrame, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "customers.csv"
    target = tmp_path / "drifted.csv"
    exported_customers.to_csv(source, index=False)
    monkeypatch.setattr("sys.argv", ["simulate", str(source), str(target), "--strength", "1"])

    simulate.main()

    drifted = pd.read_csv(target)
    assert len(drifted) == len(exported_customers)
    assert drifted["customer_id"].str.startswith("DRIFT-").all()


class TestReportScript:
    def test_exits_with_code_1_and_saves_html_when_alert(
        self,
        exported_customers: pd.DataFrame,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        reference = tmp_path / "customers.csv"
        current = tmp_path / "drifted.csv"
        html = tmp_path / "report.html"
        exported_customers.to_csv(reference, index=False)
        simulate.apply_drift(exported_customers).to_csv(current, index=False)
        monkeypatch.setattr("sys.argv", ["report", str(reference), str(current), "--html", str(html)])

        with pytest.raises(SystemExit) as exit_info:
            report.main()

        assert exit_info.value.code == 1
        assert "ALERT: yes" in capsys.readouterr().out
        assert "<html" in html.read_text(encoding="utf-8").lower()

    def test_exits_with_code_0_without_alert(
        self,
        exported_customers: pd.DataFrame,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        reference = tmp_path / "customers.csv"
        exported_customers.to_csv(reference, index=False)
        monkeypatch.setattr("sys.argv", ["report", str(reference), str(reference)])

        with pytest.raises(SystemExit) as exit_info:
            report.main()

        assert exit_info.value.code == 0
        assert "ALERT: no" in capsys.readouterr().out
