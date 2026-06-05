from __future__ import annotations

import pytest

from dlg._config import TelemetryConfig
from dlg._telemetry import setup_telemetry


def test_setup_telemetry_none() -> None:
    setup_telemetry(None)


def test_setup_telemetry_disabled() -> None:
    cfg = TelemetryConfig(enabled=False, provider="langsmith")
    setup_telemetry(cfg)


def test_setup_telemetry_langsmith(caplog: object) -> None:
    import logging

    cfg = TelemetryConfig(enabled=True, provider="langsmith")
    with __import__("contextlib").suppress(Exception):
        setup_telemetry(cfg)


def test_setup_telemetry_custom_missing_module() -> None:
    import logging

    cfg = TelemetryConfig(enabled=True, provider="custom", module_path=None, class_name=None)
    setup_telemetry(cfg)


def test_setup_telemetry_langsmith_enabled() -> None:
    cfg = TelemetryConfig(enabled=True, provider="langsmith")
    setup_telemetry(cfg)
