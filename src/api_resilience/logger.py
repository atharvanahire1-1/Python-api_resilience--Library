"""Lightweight logging configuration for api-resilience.

Emits WARNING-level messages to the console whenever a retry is triggered,
giving operators visibility into transient failures without flooding logs.
"""

import logging

_LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"


def get_logger(name: str = "api_resilience") -> logging.Logger:
    """Return a pre-configured logger for the library.

    The logger writes WARNING (and above) messages to *stderr* via a
    :class:`~logging.StreamHandler`.  If the logger already has handlers
    (e.g. the caller configured logging globally), no duplicate handler
    is added.

    Parameters
    ----------
    name:
        Logger name.  Defaults to ``"api_resilience"``.

    Returns
    -------
    logging.Logger
        A configured logger instance.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.WARNING)
        formatter = logging.Formatter(_LOG_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Allow WARNING+ through even if the root logger level is higher.
    if logger.level == logging.NOTSET:
        logger.setLevel(logging.WARNING)

    return logger
