import io


def svg_to_png_image(svg_string: str):
    """Return a PIL Image from an SVG string."""
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPM
    drawing = svg2rlg(io.StringIO(svg_string))
    if drawing is None:
        raise ValueError("Invalid SVG data")
    return renderPM.drawToPIL(drawing)


def svg_to_pdf_bytes(svg_string: str) -> bytes:
    """Return PDF bytes created from the given SVG string."""
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPDF
    drawing = svg2rlg(io.StringIO(svg_string))
    if drawing is None:
        raise ValueError("Invalid SVG data")
    try:
        pdf_bytes = renderPDF.drawToString(drawing)
    except AttributeError:  # fallback for older versions
        buffer = io.BytesIO()
        renderPDF.drawToFile(drawing, buffer)
        pdf_bytes = buffer.getvalue()
    return pdf_bytes
