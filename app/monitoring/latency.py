import argparse
import json
import statistics
import time
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


def measure(url: str, requests: int, warmup: int) -> list[float]:
    body = json.dumps(SAMPLE_CUSTOMER).encode()
    headers = {"Content-Type": "application/json"}
    durations: list[float] = []
    for i in range(warmup + requests):
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        started = time.perf_counter()
        with urllib.request.urlopen(request) as response:
            response.read()
        elapsed_ms = (time.perf_counter() - started) * 1000
        if i >= warmup:
            durations.append(elapsed_ms)
    return durations


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure the latency of POST /predict")
    parser.add_argument("--url", default="http://127.0.0.1:8000/predict")
    parser.add_argument("--requests", type=int, default=200, help="measured requests")
    parser.add_argument("--warmup", type=int, default=10, help="requests sent first and ignored")
    args = parser.parse_args()

    stats = summarize(measure(args.url, args.requests, args.warmup))
    print(f"{args.requests} requests to {args.url} (after {args.warmup} warm-up requests), ms:")
    for name, value in stats.items():
        print(f"  {name:<5} {value:8.2f}")


if __name__ == "__main__":
    main()
