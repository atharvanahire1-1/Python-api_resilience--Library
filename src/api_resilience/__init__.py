"""api-resilience — Robust decorators for transient-error handling.

Quick start::

    from api_resilience import retry_with_backoff

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def call_api():
        ...
"""

from api_resilience.decorators import retry_with_backoff

__all__ = ["retry_with_backoff"]
__version__ = "1.0.0"
