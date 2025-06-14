import importlib
import sys
import types
import pytest

class DummyImage:
    def save(self, path):
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


def test_print_label_unsupported(monkeypatch):
    pu = _load_print_utils()
    monkeypatch.setattr(pu.platform, 'system', lambda: 'Other')
    with pytest.raises(RuntimeError):
        pu.print_label(DummyImage(), 'dummy')


def test_print_label_missing_dependency(monkeypatch):
    pu = _load_print_utils(with_win32=False, with_cups=False)
    monkeypatch.setattr(pu.platform, 'system', lambda: 'Windows')
    with pytest.raises(RuntimeError):
        pu.print_label(DummyImage(), 'dummy')


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
    pu = _load_print_utils()
    tmp = DummyTmp('win_tmp')
    monkeypatch.setattr(pu.platform, 'system', lambda: 'Windows')
    monkeypatch.setattr(pu.tempfile, 'NamedTemporaryFile', lambda delete=False, suffix='': tmp)
    monkeypatch.setattr(pu, 'win32print', types.SimpleNamespace(
        OpenPrinter=lambda p: 'h',
        StartDocPrinter=lambda h, lvl, info: None,
        StartPagePrinter=lambda h: None,
        WritePrinter=lambda h, data: None,
        EndPagePrinter=lambda h: None,
        EndDocPrinter=lambda h: None,
        ClosePrinter=lambda h: None,
    ), raising=False)
    unlinked = []
    monkeypatch.setattr(pu.os, 'unlink', lambda path: unlinked.append(path))
    monkeypatch.setattr('builtins.open', lambda *args, **kwargs: DummyFile())

    pu.print_label(DummyImage(), 'dummy')

    assert tmp.closed
    assert unlinked == [tmp.name]


def test_print_label_cups_cleanup(monkeypatch):
    pu = _load_print_utils()
    tmp = DummyTmp('cups_tmp')
    monkeypatch.setattr(pu.platform, 'system', lambda: 'Linux')
    monkeypatch.setattr(pu.tempfile, 'NamedTemporaryFile', lambda delete=False, suffix='': tmp)
    monkeypatch.setattr(pu, 'cups', types.SimpleNamespace(
        Connection=lambda: types.SimpleNamespace(printFile=lambda *a, **kw: None)
    ))
    unlinked = []
    monkeypatch.setattr(pu.os, 'unlink', lambda path: unlinked.append(path))

    pu.print_label(DummyImage(), 'dummy')

    assert tmp.closed
    assert unlinked == [tmp.name]


def test_print_file_unsupported(monkeypatch):
    pu = _load_print_utils()
    monkeypatch.setattr(pu.platform, 'system', lambda: 'Other')
    with pytest.raises(RuntimeError):
        pu.print_file('dummy.pdf', 'printer')


def test_print_file_missing_dependency(monkeypatch):
    pu = _load_print_utils(with_win32=False, with_cups=False)
    monkeypatch.setattr(pu.platform, 'system', lambda: 'Linux')
    with pytest.raises(RuntimeError):
        pu.print_file('dummy.pdf', 'printer')


def test_print_file_windows(monkeypatch):
    pu = _load_print_utils()
    monkeypatch.setattr(pu.platform, 'system', lambda: 'Windows')
    calls = {}
    monkeypatch.setattr(pu, 'win32print', types.SimpleNamespace(
        OpenPrinter=lambda p: calls.setdefault('open', True) or 'h',
        StartDocPrinter=lambda *a: calls.setdefault('startdoc', True),
        StartPagePrinter=lambda *a: calls.setdefault('startpage', True),
        WritePrinter=lambda *a: calls.setdefault('write', True),
        EndPagePrinter=lambda *a: calls.setdefault('endpage', True),
        EndDocPrinter=lambda *a: calls.setdefault('enddoc', True),
        ClosePrinter=lambda *a: calls.setdefault('close', True),
    ), raising=False)
    class DummyR:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            pass
        def read(self):
            return b''

    with monkeypatch.context() as m:
        m.setattr('builtins.open', lambda *a, **k: DummyR())
        pu.print_file('dummy.pdf', 'printer')
    assert calls.get('close')


def test_print_file_cups(monkeypatch):
    pu = _load_print_utils()
    monkeypatch.setattr(pu.platform, 'system', lambda: 'Linux')
    printed = {}
    monkeypatch.setattr(pu, 'cups', types.SimpleNamespace(
        Connection=lambda: types.SimpleNamespace(printFile=lambda p, f, t, o: printed.setdefault('file', f))
    ))
    pu.print_file('dummy.pdf', 'printer')
    assert printed.get('file') == 'dummy.pdf'

