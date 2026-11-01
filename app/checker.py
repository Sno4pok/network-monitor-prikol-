import socket
import time
from dataclasses import dataclass

import requests
import yaml


@dataclass
class CheckResult:
    """Result of a single host check."""

    name: str
    target: str
    is_up: bool
    response_time_ms: float | None = None
    status_code: int | None = None
    error: str | None = None


def check_http(name: str, url: str, timeout: float = 5.0) -> CheckResult:
    """Check a website via HTTP GET request."""
    start = time.perf_counter()
    try:
        response = requests.get(url, timeout=timeout)
        elapsed_ms = (time.perf_counter() - start) * 1000
        return CheckResult(
            name=name,
            target=url,
            is_up=response.status_code < 400,
            response_time_ms=round(elapsed_ms, 1),
            status_code=response.status_code,
        )
    except requests.exceptions.Timeout:
        return CheckResult(name=name, target=url, is_up=False, error="Timeout")
    except requests.exceptions.RequestException as e:
        return CheckResult(name=name, target=url, is_up=False, error=str(e))


def check_tcp(name: str, host: str, port: int, timeout: float = 5.0) -> CheckResult:
    """Check if a TCP port is open."""
    target = f"{host}:{port}"
    start = time.perf_counter()
    try:
        conn = socket.create_connection((host, port), timeout=timeout)
        conn.close()
        elapsed_ms = (time.perf_counter() - start) * 1000
        return CheckResult(
            name=name,
            target=target,
            is_up=True,
            response_time_ms=round(elapsed_ms, 1),
        )
    except OSError as e:
        return CheckResult(name=name, target=target, is_up=False, error=str(e))


def load_hosts(path: str = "config/hosts.yaml") -> list[dict]:
    """Read the list of hosts from a YAML file."""
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["hosts"]


def run_checks(hosts: list[dict]) -> list[CheckResult]:
    """Run the proper check for every host."""
    results = []
    for host in hosts:
        if host["type"] == "http":
            result = check_http(host["name"], host["url"])
        elif host["type"] == "tcp":
            result = check_tcp(host["name"], host["host"], host["port"])
        else:
            result = CheckResult(
                name=host["name"],
                target="-",
                is_up=False,
                error=f"Unknown check type: {host['type']}",
            )
        results.append(result)
    return results


def print_results(results: list[CheckResult]) -> None:
    """Print results to the console as an aligned table."""
    for r in results:
        status = "[UP]" if r.is_up else "[DOWN]"
        if r.is_up:
            code = r.status_code if r.status_code is not None else "-"
            details = f"{code:<5} {r.response_time_ms} ms"
        else:
            details = (r.error or "Unknown error")[:60]
        print(f"{status:<8}{r.name:<22}{details}")

    up = sum(1 for r in results if r.is_up)
    down = len(results) - up
    print(f"\n{up} UP, {down} DOWN")


if __name__ == "__main__":
    hosts = load_hosts()
    results = run_checks(hosts)
    print_results(results)