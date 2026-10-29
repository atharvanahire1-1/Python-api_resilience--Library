# api-resilience

> Robust Python decorators for automatic retry with **exponential backoff** and **jitter** — designed to handle transient network errors and API rate limits gracefully.

[![CI](https://github.com/your-username/api-resilience/actions/workflows/python-app.yml/badge.svg)](https://github.com/your-username/api-resilience/actions/workflows/python-app.yml)
[![PyPI](https://img.shields.io/pypi/v/api-resilience)](https://pypi.org/project/api-resilience/)
[![Python](https://img.shields.io/pypi/pyversions/api-resilience)](https://pypi.org/project/api-resilience/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ Features

- **Exponential backoff** — delays grow as `base_delay × 2ⁿ`, capped at `max_delay`.
- **Random jitter** — each delay adds `uniform(0, jitter)` seconds to prevent the thundering-herd problem.
- **Configurable exceptions** — choose exactly which error types trigger a retry.
- **Zero dependencies** — works with the stdlib alone; optional `requests` integration out of the box.
- **Transparent** — logs every retry at `WARNING` level so you always know what's happening.

---

## 📦 Installation

```bash
pip install api-resilience
```

To include support for auto-catching `requests` exceptions:

```bash
pip install api-resilience[requests]
```

---

## 🚀 Quick Start

```python
import requests
from api_resilience import retry_with_backoff

@retry_with_backoff(max_retries=3, base_delay=1.0)
def fetch_user(user_id: int) -> dict:
    """Fetch a user from the API, automatically retrying on transient errors."""
    response = requests.get(
        f"https://api.example.com/users/{user_id}",
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


# Use it just like a normal function — retries are handled transparently.
user = fetch_user(42)
print(user)
```

When the HTTP call fails with a transient error (connection reset, timeout, 5xx), you'll see:

```
2026-10-29 11:30:00 | api_resilience | WARNING | Retry 1/3 for fetch_user after 1.37s (delay=1.00 + jitter=0.37) — ConnectionError: Connection reset
```

---

## ⚙️ Configuration

| Parameter     | Type                          | Default                                  | Description                                                   |
|---------------|-------------------------------|------------------------------------------|---------------------------------------------------------------|
| `max_retries` | `int`                         | `3`                                      | Number of retry attempts after the first failure.             |
| `base_delay`  | `float`                       | `1.0`                                    | Initial delay in seconds before the first retry.              |
| `max_delay`   | `float`                       | `60.0`                                   | Upper bound for any single delay.                             |
| `jitter`      | `float`                       | `1.0`                                    | Max random seconds added to each delay (thundering-herd fix). |
| `exceptions`  | `tuple[type[BaseException]]`  | Transient network errors (see below)     | Exception types that trigger a retry.                         |

### Default retryable exceptions

| Standard Library          | `requests` (when installed)          |
|---------------------------|--------------------------------------|
| `ConnectionError`         | `requests.exceptions.ConnectionError`|
| `TimeoutError`            | `requests.exceptions.Timeout`        |
| `OSError`                 | `requests.exceptions.HTTPError`      |

---

## 📖 Advanced Usage

### Custom exception list

```python
from api_resilience import retry_with_backoff
from requests.exceptions import HTTPError, Timeout

@retry_with_backoff(
    max_retries=5,
    base_delay=0.5,
    max_delay=30.0,
    jitter=2.0,
    exceptions=(HTTPError, Timeout),
)
def post_event(payload: dict) -> dict:
    resp = requests.post("https://api.example.com/events", json=payload, timeout=5)
    resp.raise_for_status()
    return resp.json()
```

### Wrapping any callable

The decorator works with **any** function — not just HTTP calls:

```python
import sqlite3
from api_resilience import retry_with_backoff

@retry_with_backoff(max_retries=3, base_delay=0.1, exceptions=(sqlite3.OperationalError,))
def query_db(sql: str):
    conn = sqlite3.connect("app.db")
    return conn.execute(sql).fetchall()
```

---

## 🧪 Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run the test suite
pytest -v
```

---

## 📁 Project Structure

```
api-resilience/
├── .github/
│   └── workflows/
│       └── python-app.yml      # CI pipeline
├── src/
│   └── api_resilience/
│       ├── __init__.py          # Public API — exports retry_with_backoff
│       ├── decorators.py        # Core retry logic
│       └── logger.py            # Lightweight logging setup
├── tests/
│   └── test_decorators.py       # Full test suite (pytest)
├── pyproject.toml               # Modern packaging config
└── README.md                    # This file
```

---

## 📄 License

[MIT](https://opensource.org/licenses/MIT) — free for personal and commercial use.
