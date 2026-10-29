"""Core retry decorator with exponential backoff and jitter.

This module provides :func:`retry_with_backoff`, a flexible decorator that
automatically retries a callable when it raises a matched exception.  It
uses *exponential backoff* capped at a configurable ceiling and adds
*random jitter* to each delay to prevent the **thundering-herd** problem
when many clients retry simultaneously.
"""

from __future__ import annotations

import functools
import random
import time
from typing import Any, Callable, Tuple, Type

from api_resilience.logger import get_logger

logger = get_logger()

# ---------------------------------------------------------------------------
# Default exception types that signal a *transient* failure
# ---------------------------------------------------------------------------
# We intentionally keep ``requests`` as an optional dependency.  When it is
# installed the decorator can catch its common transient exceptions
# out-of-the-box; otherwise callers must supply their own ``exceptions``.

_DEFAULT_EXCEPTIONS: Tuple[Type[BaseException], ...] = (ConnectionError, TimeoutError, OSError)

try:
    import requests.exceptions as _req_exc

    _DEFAULT_EXCEPTIONS = (
        *_DEFAULT_EXCEPTIONS,
        _req_exc.ConnectionError,
        _req_exc.Timeout,
        _req_exc.HTTPError,
    )
except ImportError:  # requests is not installed
    pass


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: float = 1.0,
    exceptions: Tuple[Type[BaseException], ...] | None = None,
) -> Callable:
    """Decorator that retries a function on transient failures.

    Parameters
    ----------
    max_retries:
        Maximum number of retry attempts **after** the first failure.
        A value of ``3`` means the function can execute up to 4 times
        in total (1 initial + 3 retries).
    base_delay:
        Initial delay in seconds before the first retry.  Subsequent
        delays grow exponentially: ``base_delay * 2 ** attempt``.
    max_delay:
        Upper bound in seconds for any single delay.
    jitter:
        Maximum additional random seconds added to each delay.  A
        uniform value in ``[0, jitter)`` is drawn every retry to spread
        out concurrent retries (*thundering-herd mitigation*).
    exceptions:
        Tuple of exception classes that are considered **retryable**.
        When ``None``, the decorator catches common transient network
        exceptions (``ConnectionError``, ``TimeoutError``, ``OSError``
        and, if *requests* is installed, ``requests.exceptions.ConnectionError``,
        ``requests.exceptions.Timeout``, and ``requests.exceptions.HTTPError``).

    Returns
    -------
    Callable
        A decorator wrapping the target function with retry logic.

    Raises
    ------
    TypeError
        If ``max_retries`` is not a non-negative integer, or if
        ``base_delay`` / ``max_delay`` / ``jitter`` are not non-negative
        numbers.

    Examples
    --------
    >>> import requests
    >>> from api_resilience import retry_with_backoff
    >>>
    >>> @retry_with_backoff(max_retries=5, base_delay=0.5)
    ... def fetch(url: str):
    ...     response = requests.get(url, timeout=10)
    ...     response.raise_for_status()
    ...     return response.json()
    """

    # ---- Validate parameters ------------------------------------------------
    if not isinstance(max_retries, int) or max_retries < 0:
        raise TypeError(f"max_retries must be a non-negative integer, got {max_retries!r}")
    for name, value in [("base_delay", base_delay), ("max_delay", max_delay), ("jitter", jitter)]:
        if not isinstance(value, (int, float)) or value < 0:
            raise TypeError(f"{name} must be a non-negative number, got {value!r}")

    if exceptions is None:
        exceptions = _DEFAULT_EXCEPTIONS

    def decorator(func: Callable) -> Callable:
        # Resolve the display name once so it works with mocks and lambdas too.
        _func_name = getattr(func, "__qualname__", None) or getattr(func, "__name__", repr(func))

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: BaseException | None = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exception = exc

                    if attempt == max_retries:
                        logger.warning(
                            "All %d retries exhausted for %s. Raising last exception.",
                            max_retries,
                            _func_name,
                        )
                        raise

                    delay = min(base_delay * (2 ** attempt), max_delay)
                    actual_jitter = random.uniform(0, jitter)
                    total_delay = delay + actual_jitter

                    logger.warning(
                        "Retry %d/%d for %s after %.2fs (delay=%.2f + jitter=%.2f) — %s: %s",
                        attempt + 1,
                        max_retries,
                        _func_name,
                        total_delay,
                        delay,
                        actual_jitter,
                        type(exc).__name__,
                        exc,
                    )
                    time.sleep(total_delay)

            # Should never be reached, but satisfies type-checkers.
            raise last_exception  # type: ignore[misc]

        return wrapper

    return decorator
