import builtins
import importlib
from types import SimpleNamespace

import sys

# Provide a minimal 'requests' module for import
class DummyResponse:
    def __init__(self, data):
        self._data = data
    def raise_for_status(self):
        pass
    def json(self):
        return self._data

def dummy_get(url, params=None, json=None, timeout=10):
    return DummyResponse({"result": "ok", "params": params, "json": json})

requests_mod = SimpleNamespace(get=dummy_get)
sys.modules['requests'] = requests_mod

calserver_api = importlib.import_module('app.calserver_api')


def test_fetch_calibration_data():
    data = calserver_api.fetch_calibration_data(
        "http://example.com",
        "user",
        "pass",
        "key",
        {"foo": 1},
    )
    assert data["result"] == "ok"
    assert data["params"]["username"] == "user"
    assert data["json"] == {"foo": 1}
