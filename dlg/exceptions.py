from __future__ import annotations


class DLGError(Exception):
    def __init__(self, message: str, context: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.context: dict = context or {}


class GraphValidationError(DLGError):
    pass


class StaticLoopException(GraphValidationError):
    pass


class UnreachableNodeException(GraphValidationError):
    pass


class MixedRoutingConflict(GraphValidationError):
    pass


class SendTargetError(GraphValidationError):
    pass


class SubgraphCompatibilityError(GraphValidationError):
    pass


class NodeTimeoutException(DLGError):
    pass


class CheckpointerMissingError(DLGError):
    pass


class SchemaVersionMismatch(DLGError):
    pass
