import json
from typing import Any

import pytest

from app.monitoring import latency


class TestSummarize:
    def test_basic_statistics(self) -> None:
        stats = latency.summarize([float(i) for i in range(1, 101)])

        assert stats["mean"] == pytest.approx(50.5)
        assert stats["p50"] == 50
        assert stats["p95"] == 95
        assert stats["p99"] == 99
        assert stats["max"] == 100

    def test_single_value(self) -> None:
        stats = latency.summarize([12.5])

        assert stats == {"mean": 12.5, "p50": 12.5, "p95": 12.5, "p99": 12.5, "max": 12.5}

    def test_input_order_does_not_matter(self) -> None:
        assert latency.summarize([3.0, 1.0, 2.0]) == latency.summarize([1.0, 2.0, 3.0])


class FakeResponse:
    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return b"{}"


def test_measure_skips_warmup_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: list[Any] = []

    def fake_urlopen(request: Any) -> FakeResponse:
        sent.append(request)
        return FakeResponse()

    monkeypatch.setattr("app.monitoring.latency.urllib.request.urlopen", fake_urlopen)

    durations = latency.measure("http://example/predict", requests=5, warmup=2)

    assert len(durations) == 5
    assert len(sent) == 7
    assert json.loads(sent[0].data) == latency.SAMPLE_CUSTOMER
    assert sent[0].get_method() == "POST"


def test_main_prints_a_summary(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr("app.monitoring.latency.measure", lambda url, requests, warmup: [1.0, 2.0, 3.0])
    monkeypatch.setattr("sys.argv", ["latency", "--requests", "3", "--warmup", "0"])

    latency.main()

    out = capsys.readouterr().out
    assert "p95" in out
    assert "mean" in out
