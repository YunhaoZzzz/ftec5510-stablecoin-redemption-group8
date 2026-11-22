"""Deterministic redemption allocation rules."""

from __future__ import annotations

from collections.abc import Sequence


def allocate_fcfs(available: float, requests: Sequence[float]) -> list[float]:
    """Allocate available liquidity in request order."""
    _validate(available, requests)
    remaining = available
    allocations = []
    for request in requests:
        paid = min(request, remaining)
        allocations.append(paid)
        remaining -= paid
    return allocations


def allocate_pro_rata(available: float, requests: Sequence[float]) -> list[float]:
    """Allocate the same share of each request, capped at full payment."""
    _validate(available, requests)
    total = sum(requests)
    if total == 0:
        return [0.0 for _ in requests]
    share = min(1.0, available / total)
    return [request * share for request in requests]


def allocate(rule: str, available: float, requests: Sequence[float]) -> list[float]:
    """Dispatch by rule name."""
    if rule == "fcfs":
        return allocate_fcfs(available, requests)
    if rule == "pro_rata":
        return allocate_pro_rata(available, requests)
    raise ValueError(f"Unknown redemption rule: {rule}")


def _validate(available: float, requests: Sequence[float]) -> None:
    if available < 0:
        raise ValueError("available must be non-negative")
    if any(request < 0 for request in requests):
        raise ValueError("requests must be non-negative")
