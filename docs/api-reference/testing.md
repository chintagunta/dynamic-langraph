# DLGTestHarness API Reference

## Methods

| Method | Description |
|--------|-------------|
| `test_node(handler_fn, state_dict, *, config=None) -> dict` | Sync wrapper — runs single node, returns state delta. |
| `atest_node(handler_fn, state_dict, *, config=None) -> dict` | Async version. |
| `assert_state_delta(result, expected) -> None` | Asserts result contains expected keys/values. |

## Example

```python
from dlg import DLGTestHarness

def my_node(state):
    return {"result": state["message"].upper()}

result = DLGTestHarness.test_node(my_node, {"message": "hello", "result": ""})
DLGTestHarness.assert_state_delta(result, {"result": "HELLO"})
```
