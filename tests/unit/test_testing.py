from __future__ import annotations

import pytest

from dlg.testing import DLGTestHarness


def sync_handler(state: dict) -> dict:
    return {"result": f"Hello: {state.get('message', '')}"}


async def async_handler(state: dict) -> dict:
    return {"result": f"Async: {state.get('message', '')}"}


async def test_test_node_sync_handler() -> None:
    result = await DLGTestHarness.atest_node(sync_handler, {"message": "world", "result": ""})
    assert result.get("result") == "Hello: world"


async def test_test_node_async_handler() -> None:
    result = await DLGTestHarness.atest_node(async_handler, {"message": "world", "result": ""})
    assert result.get("result") == "Async: world"


def test_assert_state_delta_passes() -> None:
    DLGTestHarness.assert_state_delta({"result": "Hello: world"}, {"result": "Hello: world"})


def test_assert_state_delta_fails_on_mismatch() -> None:
    with pytest.raises(AssertionError):
        DLGTestHarness.assert_state_delta({"result": "wrong"}, {"result": "expected"})


def test_assert_state_delta_fails_on_missing_key() -> None:
    with pytest.raises(AssertionError):
        DLGTestHarness.assert_state_delta({}, {"result": "something"})
