from __future__ import annotations

from typing import Annotated

from typing_extensions import TypedDict


def _merge_lists(a: list, b: list) -> list:
    return a + b


class FanOutState(TypedDict):
    items: list[str]
    results: Annotated[list[str], _merge_lists]
