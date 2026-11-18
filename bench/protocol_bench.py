"""Minimal local protocol benchmark with transparent measurement limits."""

from __future__ import annotations

import argparse
import csv
import json
import socket
import statistics
import time
import urllib.error
import urllib.request
from pathlib import Path


def benchmark_http(url: str, payload: bytes, count: int) -> list[float]:
    latencies = []
    for _ in range(count):
        request = urllib.request.Request(url, data=payload, method="POST", headers={"Content-Type": "application/json"})
        started = time.perf_counter()
        with urllib.request.urlopen(request, timeout=5):
            pass
        latencies.append((time.perf_counter() - started) * 1000)
    return latencies


def benchmark_tcp(host: str, port: int, payload: bytes, count: int) -> list[float]:
    latencies = []
    for _ in range(count):
        started = time.perf_counter()
        with socket.create_connection((host, port), timeout=5) as connection:
            connection.sendall(payload)
        latencies.append((time.perf_counter() - started) * 1000)
    return latencies


def summarize(protocol: str, latencies: list[float], payload_bytes: int, note: str) -> dict[str, object]:
    return {
        "protocol": protocol,
        "messages": len(latencies),
        "success_rate": 1.0,
        "payload_bytes": payload_bytes,
        "average_latency_ms": statistics.mean(latencies),
        "median_latency_ms": statistics.median(latencies),
        "p95_latency_ms": sorted(latencies)[max(0, int(len(latencies) * 0.95) - 1)],
        "max_latency_ms": max(latencies),
        "measurement_note": note,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--http-url", default="http://127.0.0.1:8081/bench")
    parser.add_argument("--output", default="results/protocols/protocol_comparison.csv")
    args = parser.parse_args()
    payload = json.dumps({"timestamp": "2025-01-01T00:00:00Z", "soil_moisture": 42.0}).encode()
    rows = []
    try:
        rows.append(summarize("HTTP", benchmark_http(args.http_url, payload, args.count), len(payload), "Measured application latency; server must be running."))
    except (OSError, urllib.error.URLError) as exc:
        rows.append({"protocol": "HTTP", "messages": args.count, "success_rate": 0.0, "payload_bytes": len(payload), "measurement_note": f"Unavailable: {exc}"})
    try:
        rows.append(summarize("TCP connection", benchmark_tcp("127.0.0.1", 1884, payload, args.count), len(payload), "Connection timing only; not a substitute for MQTT packet capture."))
    except OSError as exc:
        rows.append({"protocol": "TCP connection", "messages": args.count, "success_rate": 0.0, "payload_bytes": len(payload), "measurement_note": f"Unavailable: {exc}"})
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=sorted({key for row in rows for key in row}))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote benchmark results to {output}")


if __name__ == "__main__":
    main()
