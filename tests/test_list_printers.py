import importlib
import sys
import types
import pytest


class DummyImage:
    pass


def _load_print_utils(with_win32=True, with_cups=True):
    pil_mod = types.ModuleType("PIL")
    pil_image_mod = types.ModuleType("PIL.Image")
    pil_image_mod.Image = DummyImage
    pil_mod.Image = pil_image_mod
    sys.modules["PIL"] = pil_mod
    sys.modules["PIL.Image"] = pil_image_mod

    if with_win32:
        sys.modules["win32print"] = types.ModuleType("win32print")
    else:
        sys.modules.pop("win32print", None)

    if with_cups:
        sys.modules["cups"] = types.ModuleType("cups")
    else:
        sys.modules.pop("cups", None)

    if "app.print_utils" in sys.modules:
        return importlib.reload(sys.modules["app.print_utils"])
    return importlib.import_module("app.print_utils")


def test_list_printers_unknown(monkeypatch):
    pu = _load_print_utils()
    monkeypatch.setattr(pu.platform, 'system', lambda: 'Other')
    assert pu.list_printers() == []


def test_list_printers_missing_dependency(monkeypatch):
    pu = _load_print_utils(with_win32=False, with_cups=False)
    monkeypatch.setattr(pu.platform, 'system', lambda: 'Linux')
    with pytest.raises(RuntimeError):
        pu.list_printers()


