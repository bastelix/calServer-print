import importlib
import sys
import types
import pytest

# Stub PIL module for import
class DummyImage:
    def save(self, path):
        pass

pil_mod = types.ModuleType('PIL')
pil_image_mod = types.ModuleType('PIL.Image')
pil_image_mod.Image = DummyImage
pil_mod.Image = pil_image_mod
sys.modules['PIL'] = pil_mod
sys.modules['PIL.Image'] = pil_image_mod

# Stub cups and win32print modules
sys.modules['cups'] = types.ModuleType('cups')
sys.modules['win32print'] = types.ModuleType('win32print')

print_utils = importlib.import_module('app.print_utils')


def test_print_label_unsupported(monkeypatch):
    monkeypatch.setattr(print_utils.platform, 'system', lambda: 'Other')
    with pytest.raises(RuntimeError):
        print_utils.print_label(DummyImage(), 'dummy')


class DummyTmp:
    def __init__(self, name='tmp'):
        self.name = name
        self.closed = False
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        self.closed = True


class DummyFile:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        pass
    def read(self):
        return b''


def test_print_label_windows_cleanup(monkeypatch):
    tmp = DummyTmp('win_tmp')
    monkeypatch.setattr(print_utils.platform, 'system', lambda: 'Windows')
    monkeypatch.setattr(print_utils.tempfile, 'NamedTemporaryFile', lambda delete=False, suffix='': tmp)
    monkeypatch.setattr(print_utils, 'win32print', types.SimpleNamespace(
        OpenPrinter=lambda p: 'h',
        StartDocPrinter=lambda h, lvl, info: None,
        StartPagePrinter=lambda h: None,
        WritePrinter=lambda h, data: None,
        EndPagePrinter=lambda h: None,
        EndDocPrinter=lambda h: None,
        ClosePrinter=lambda h: None,
    ), raising=False)
    unlinked = []
    monkeypatch.setattr(print_utils.os, 'unlink', lambda path: unlinked.append(path))
    monkeypatch.setattr('builtins.open', lambda *args, **kwargs: DummyFile())

    print_utils.print_label(DummyImage(), 'dummy')

    assert tmp.closed
    assert unlinked == [tmp.name]


def test_print_label_cups_cleanup(monkeypatch):
    tmp = DummyTmp('cups_tmp')
    monkeypatch.setattr(print_utils.platform, 'system', lambda: 'Linux')
    monkeypatch.setattr(print_utils.tempfile, 'NamedTemporaryFile', lambda delete=False, suffix='': tmp)
    monkeypatch.setattr(print_utils, 'cups', types.SimpleNamespace(
        Connection=lambda: types.SimpleNamespace(printFile=lambda *a, **kw: None)
    ))
    unlinked = []
    monkeypatch.setattr(print_utils.os, 'unlink', lambda path: unlinked.append(path))

    print_utils.print_label(DummyImage(), 'dummy')

    assert tmp.closed
    assert unlinked == [tmp.name]

