import io


def svg_to_png_image(svg_string: str):
    """Return a PIL Image from an SVG string.

    This first tries to use ``svglib`` to parse the SVG. If that fails, a
    fallback via ``cairosvg`` is attempted when available.
    """
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPM
    from PIL import Image

    drawing = svg2rlg(io.StringIO(svg_string))
    if drawing is not None:
        return renderPM.drawToPIL(drawing)

    try:  # fallback when svglib cannot parse the SVG
        from cairosvg import svg2png
    except Exception:  # pragma: no cover - optional dependency may be missing
        raise ValueError("Invalid SVG data")

    png_bytes = svg2png(bytestring=svg_string.encode())
    return Image.open(io.BytesIO(png_bytes))


def svg_to_pdf_bytes(svg_string: str) -> bytes:
    """Return PDF bytes created from the given SVG string.

    As with :func:`svg_to_png_image`, ``svglib`` is used first and ``cairosvg``
    is attempted as a fallback.
    """
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPDF

    drawing = svg2rlg(io.StringIO(svg_string))
    if drawing is not None:
        try:
            return renderPDF.drawToString(drawing)
        except AttributeError:  # pragma: no cover - fallback for older versions
            buffer = io.BytesIO()
            renderPDF.drawToFile(drawing, buffer)
            return buffer.getvalue()

    try:  # fallback when svglib cannot parse the SVG
        from cairosvg import svg2pdf
    except Exception:  # pragma: no cover - optional dependency may be missing
        raise ValueError("Invalid SVG data")

    return svg2pdf(bytestring=svg_string.encode())
