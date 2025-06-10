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


def dummy_table_a(columns=None, rows=None, row_key=None, on_select=None, pagination=None):
    pass


def dummy_table_b(columns=None, rows=None, row_key=None, on_select=None, rows_per_page=None):
    pass


def dummy_table_c(columns=None, rows=None, row_key=None, on_select=None, selection="single"):
    pass


def test_build_table_kwargs_pagination_or_rows_per_page():
    kwargs_a = main._build_table_kwargs(dummy_table_a, [], None)
    assert kwargs_a.get('pagination') == {'rowsPerPage': 10}

    kwargs_b = main._build_table_kwargs(dummy_table_b, [], None)
    assert kwargs_b.get('rows_per_page') == 10
    assert 'pagination' not in kwargs_b


def test_build_table_kwargs_selection():
    kwargs_c = main._build_table_kwargs(dummy_table_c, [], None)
    assert kwargs_c.get('selection') == 'single'


def test_pil_to_data_url_prefix():
    class DummyImg:
        def save(self, buffer, format=None):
            buffer.write(b'test')

    result = main._pil_to_data_url(DummyImg())
    assert result.startswith('data:image/png;base64,')
