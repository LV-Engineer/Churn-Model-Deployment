import io
import json
import urllib.error
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
    monkeypatch.setattr("app.monitoring.latency.measure", lambda url, requests, warmup, delay: [1.0, 2.0, 3.0])
    monkeypatch.setattr("sys.argv", ["latency", "--requests", "3", "--warmup", "0"])

    latency.main()

    out = capsys.readouterr().out
    assert "p95" in out
    assert "mean" in out


def _rate_limited(request: Any) -> None:
    raise urllib.error.HTTPError(request.full_url, 429, "Too Many Requests", {}, io.BytesIO())  # type: ignore[arg-type]


def test_measure_gives_up_when_the_rate_limit_does_not_clear(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.monitoring.latency.urllib.request.urlopen", _rate_limited)
    monkeypatch.setattr("app.monitoring.latency.time.sleep", lambda seconds: None)

    with pytest.raises(RuntimeError, match="Rate limit"):
        latency.measure("http://example/predict", requests=1, warmup=0)


def test_measure_waits_and_retries_after_a_429(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"count": 0}
    waits: list[float] = []

    def flaky(request: Any) -> FakeResponse:
        calls["count"] += 1
        if calls["count"] == 1:
            _rate_limited(request)
        return FakeResponse()

    monkeypatch.setattr("app.monitoring.latency.urllib.request.urlopen", flaky)
    monkeypatch.setattr("app.monitoring.latency.time.sleep", waits.append)

    durations = latency.measure("http://example/predict", requests=2, warmup=0)

    assert len(durations) == 2
    assert calls["count"] == 3
    assert waits == [latency.RATE_LIMIT_WAIT]


def test_main_exits_with_a_message_on_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    def rate_limited(url: str, requests: int, warmup: int, delay: float) -> list[float]:
        raise RuntimeError("Rate limit reached (429)")

    monkeypatch.setattr("app.monitoring.latency.measure", rate_limited)
    monkeypatch.setattr("sys.argv", ["latency"])

    with pytest.raises(SystemExit, match="Rate limit"):
        latency.main()


def test_measure_pauses_between_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    pauses: list[float] = []
    monkeypatch.setattr("app.monitoring.latency.urllib.request.urlopen", lambda request: FakeResponse())
    monkeypatch.setattr("app.monitoring.latency.time.sleep", pauses.append)

    latency.measure("http://example/predict", requests=3, warmup=0, delay=0.5)

    assert pauses == [0.5, 0.5, 0.5]
