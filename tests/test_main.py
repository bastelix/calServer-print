import importlib
import sys
import types

# Provide stub modules so ``app.main`` can be imported without optional deps
pil_mod = types.ModuleType("PIL")
pil_image_mod = types.ModuleType("PIL.Image")
class DummyImage:
    pass

pil_image_mod.Image = DummyImage
pil_mod.Image = pil_image_mod
sys.modules["PIL"] = pil_mod
sys.modules["PIL.Image"] = pil_image_mod

ng_mod = types.ModuleType("nicegui")
ng_mod.ui = types.SimpleNamespace()
sys.modules["nicegui"] = ng_mod
sys.modules["nicegui.ui"] = ng_mod.ui

from app import main


def dummy_table_a(columns=None, rows=None, row_key=None, on_select=None, pagination=True):
    pass


def dummy_table_b(columns=None, rows=None, row_key=None, on_select=None):
    pass


def test_build_table_kwargs_optional_pagination():
    kwargs_a = main._build_table_kwargs(dummy_table_a, [], None)
    assert 'pagination' in kwargs_a

    kwargs_b = main._build_table_kwargs(dummy_table_b, [], None)
    assert 'pagination' not in kwargs_b
