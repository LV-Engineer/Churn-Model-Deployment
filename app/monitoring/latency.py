import argparse
import json
import statistics
import time
import urllib.error
import urllib.request

SAMPLE_CUSTOMER = {
    "gender": "Male",
    "senior_citizen": "No",
    "partner": "No",
    "dependents": "No",
    "tenure_months": 2,
    "phone_service": "Yes",
    "multiple_lines": "No",
    "internet_service": "Fiber optic",
    "online_security": "No",
    "online_backup": "No",
    "device_protection": "No",
    "tech_support": "No",
    "streaming_tv": "No",
    "streaming_movies": "No",
    "contract": "Month-to-month",
    "paperless_billing": "Yes",
    "payment_method": "Electronic check",
    "monthly_charges": 90.0,
}


def summarize(durations_ms: list[float]) -> dict[str, float]:
    """Mean and percentiles of request durations in milliseconds."""
    ordered = sorted(durations_ms)

    def percentile(share: float) -> float:
        index = max(0, min(len(ordered) - 1, round(share * len(ordered)) - 1))
        return ordered[index]

    return {
        "mean": statistics.fmean(ordered),
        "p50": percentile(0.50),
        "p95": percentile(0.95),
        "p99": percentile(0.99),
        "max": ordered[-1],
    }


RATE_LIMIT_WAIT = 60.0
MAX_RETRIES = 3


def _send(url: str, body: bytes) -> float:
    """Send one request, return its duration in milliseconds."""
    request = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request) as response:
        response.read()
    return (time.perf_counter() - started) * 1000


def measure(url: str, requests: int, warmup: int, delay: float = 0.0) -> list[float]:
    """Duration of each measured request in milliseconds.

    A 429 answer is not a measurement: the script waits for the rate limit window and repeats the request.
    """
    body = json.dumps(SAMPLE_CUSTOMER).encode()
    durations: list[float] = []
    for i in range(warmup + requests):
        for attempt in range(MAX_RETRIES + 1):
            try:
                elapsed_ms = _send(url, body)
                break
            except urllib.error.HTTPError as error:
                if error.code != 429:
                    raise
                if attempt == MAX_RETRIES:
                    raise RuntimeError(
                        "Rate limit reached (429) and it did not clear. "
                        "Use fewer requests, add --delay, or wait and run again."
                    ) from error
                print(f"Rate limit reached, waiting {RATE_LIMIT_WAIT:.0f} s before retrying", flush=True)
                time.sleep(RATE_LIMIT_WAIT)
        if i >= warmup:
            durations.append(elapsed_ms)
        if delay:
            time.sleep(delay)
    return durations


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure the latency of POST /predict")
    parser.add_argument("--url", default="http://127.0.0.1:8000/predict")
    parser.add_argument("--requests", type=int, default=50, help="measured requests")
    parser.add_argument("--warmup", type=int, default=5, help="requests sent first and ignored")
    parser.add_argument("--delay", type=float, default=0.0, help="pause between requests, seconds")
    args = parser.parse_args()

    try:
        durations = measure(args.url, args.requests, args.warmup, args.delay)
    except RuntimeError as error:
        raise SystemExit(str(error)) from error
    stats = summarize(durations)
    print(f"{args.requests} requests to {args.url} (after {args.warmup} warm-up requests), ms:")
    for name, value in stats.items():
        print(f"  {name:<5} {value:8.2f}")


if __name__ == "__main__":
    main()
