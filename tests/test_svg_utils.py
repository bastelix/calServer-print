import importlib
import sys
import types
import pytest


def _load_svg_utils(return_drawing=True, has_draw_to_string=True):
    # Setup stub modules for svglib
    svglib_mod = types.ModuleType('svglib')
    svglib_svglib_mod = types.ModuleType('svglib.svglib')
    def dummy_svg2rlg(src):
        return object() if return_drawing else None
    svglib_svglib_mod.svg2rlg = dummy_svg2rlg
    svglib_mod.svglib = svglib_svglib_mod
    sys.modules['svglib'] = svglib_mod
    sys.modules['svglib.svglib'] = svglib_svglib_mod

    # Setup stub modules for reportlab
    reportlab_mod = types.ModuleType('reportlab')
    graphics_mod = types.ModuleType('reportlab.graphics')
    renderPM_mod = types.ModuleType('reportlab.graphics.renderPM')
    renderPDF_mod = types.ModuleType('reportlab.graphics.renderPDF')
    renderPM_mod.drawToPIL = lambda drawing: ('PNG', drawing)
    if has_draw_to_string:
        renderPDF_mod.drawToString = lambda drawing: b'PDF'
    else:
        def drawToFile(drawing, buffer):
            buffer.write(b'PDF')
        renderPDF_mod.drawToFile = drawToFile
    graphics_mod.renderPM = renderPM_mod
    graphics_mod.renderPDF = renderPDF_mod
    reportlab_mod.graphics = graphics_mod
    sys.modules['reportlab'] = reportlab_mod
    sys.modules['reportlab.graphics'] = graphics_mod
    sys.modules['reportlab.graphics.renderPM'] = renderPM_mod
    sys.modules['reportlab.graphics.renderPDF'] = renderPDF_mod

    if 'app.svg_utils' in sys.modules:
        return importlib.reload(sys.modules['app.svg_utils'])
    return importlib.import_module('app.svg_utils')


def test_svg_to_png_image_success():
    su = _load_svg_utils()
    result = su.svg_to_png_image('<svg></svg>')
    assert result[0] == 'PNG'


def test_svg_to_png_image_invalid():
    su = _load_svg_utils(return_drawing=False)
    with pytest.raises(ValueError):
        su.svg_to_png_image('<svg></svg>')


def test_svg_to_pdf_bytes_default():
    su = _load_svg_utils()
    assert su.svg_to_pdf_bytes('<svg></svg>') == b'PDF'


def test_svg_to_pdf_bytes_fallback():
    su = _load_svg_utils(has_draw_to_string=False)
    assert su.svg_to_pdf_bytes('<svg></svg>') == b'PDF'
