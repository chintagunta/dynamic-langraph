from __future__ import annotations

import logging

from dlg._config import TelemetryConfig

logger = logging.getLogger(__name__)


def setup_telemetry(config: TelemetryConfig | None) -> None:
    if config is None or not config.enabled:
        return

    if config.provider == "langsmith":
        logger.info(
            "LangSmith tracing enabled via LANGSMITH_TRACING + LANGSMITH_API_KEY env vars"
        )
        return

    if config.provider == "custom":
        if config.module_path is None or config.class_name is None:
            logger.warning("Custom telemetry provider requires module_path and class_name")
            return
        import importlib

        mod = importlib.import_module(config.module_path)
        cls = getattr(mod, config.class_name)
        cls()
        logger.info(f"Custom telemetry provider '{config.class_name}' initialized")
