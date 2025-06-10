import importlib
import sys
import types
import io
import pytest


def _load_svg_utils(return_drawing=True, has_draw_to_string=True, has_cairosvg=True):
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

    # Minimal PIL stub so svg_utils can open PNG bytes
    pil_mod = types.ModuleType('PIL')
    pil_image_mod = types.ModuleType('PIL.Image')
    pil_image_mod.open = lambda buffer: ('IMG', buffer)
    pil_mod.Image = pil_image_mod
    sys.modules['PIL'] = pil_mod
    sys.modules['PIL.Image'] = pil_image_mod

    if has_cairosvg:
        cairosvg_mod = types.ModuleType('cairosvg')
        PNG_BYTES = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\nIDAT'
            b'\x08\xd7c\xf8\x0f\x00\x01\x05\x01\x02\xa7~\xcd\xd1\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        cairosvg_mod.svg2png = lambda bytestring=None, **kwargs: PNG_BYTES
        cairosvg_mod.svg2pdf = lambda bytestring=None, **kwargs: b'%PDF'
        sys.modules['cairosvg'] = cairosvg_mod
    else:
        sys.modules.pop('cairosvg', None)

    if 'app.svg_utils' in sys.modules:
        return importlib.reload(sys.modules['app.svg_utils'])
    return importlib.import_module('app.svg_utils')


def test_svg_to_png_image_success():
    su = _load_svg_utils()
    result = su.svg_to_png_image('<svg></svg>')
    assert result[0] == 'PNG'


def test_svg_to_png_image_invalid():
    su = _load_svg_utils(return_drawing=False, has_cairosvg=False)
    with pytest.raises(ValueError):
        su.svg_to_png_image('<svg></svg>')


def test_svg_to_png_image_cairosvg_fallback():
    su = _load_svg_utils(return_drawing=False, has_cairosvg=True)
    img = su.svg_to_png_image('<svg></svg>')
    assert img[0] == 'IMG'


def test_svg_to_png_image_no_cairosvg():
    su = _load_svg_utils(return_drawing=False, has_cairosvg=False)
    with pytest.raises(ValueError):
        su.svg_to_png_image('<svg></svg>')


def test_svg_to_pdf_bytes_default():
    su = _load_svg_utils()
    assert su.svg_to_pdf_bytes('<svg></svg>') == b'PDF'


def test_svg_to_pdf_bytes_fallback():
    su = _load_svg_utils(has_draw_to_string=False)
    assert su.svg_to_pdf_bytes('<svg></svg>') == b'PDF'


def test_svg_to_pdf_bytes_cairosvg():
    su = _load_svg_utils(return_drawing=False)
    assert su.svg_to_pdf_bytes('<svg></svg>') == b'%PDF'
