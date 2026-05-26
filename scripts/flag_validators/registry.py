"""Registry of custom flag validators for shell1_flags CTFd plugin."""

from __future__ import annotations

import re
from typing import Any, Callable

ValidatorFn = Callable[[str, dict[str, Any]], bool]

_REGISTRY: dict[str, ValidatorFn] = {}


def register(name: str, fn: ValidatorFn) -> None:
    _REGISTRY[name] = fn


def get(name: str) -> ValidatorFn | None:
    return _REGISTRY.get(name)


def check(name: str, submission: str, context: dict[str, Any]) -> bool:
    fn = get(name)
    if fn is None:
        return False
    return fn(submission.strip(), context)


def _delivery_101(submission: str, context: dict[str, Any]) -> bool:
    """Accept hidden livrable path flag; file check on /mnt/host is future work."""
    pattern = r"^shell1\{\.delivery_101\.tar\}$"
    return bool(re.match(pattern, submission, re.IGNORECASE))


register("delivery_101", _delivery_101)
