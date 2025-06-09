"""Helpers for listing printers and printing images across platforms."""

import platform
from typing import List
from PIL import Image


win32print = None
cups = None

if platform.system() == "Windows":
    try:  # pragma: no cover - optional dependency may be missing
        import win32print as _win32print
        win32print = _win32print
    except ImportError:  # pragma: no cover - handled below
        win32print = None
elif platform.system() in ("Linux", "Darwin"):
    try:  # pragma: no cover - optional dependency may be missing
        import cups as _cups
        cups = _cups
    except ImportError:  # pragma: no cover - handled below
        cups = None


def list_printers() -> List[str]:
    """Return a list of available printer names."""

    if platform.system() == "Windows":
        if not win32print:
            raise RuntimeError("win32print is required on Windows")
        return [p[2] for p in win32print.EnumPrinters(2)]
    elif platform.system() in ("Linux", "Darwin"):
        if not cups:
            raise RuntimeError("cups is required on this platform")
        conn = cups.Connection()
        return list(conn.getPrinters().keys())
    return []


def print_label(image: Image.Image, printer_name: str) -> None:
    """Send the given image to ``printer_name``.

    The implementation handles Windows and CUPS based systems. For other
    platforms a ``RuntimeError`` is raised.
    """

    if platform.system() == "Windows":
        if not win32print:
            raise RuntimeError("win32print is required on Windows")
        import tempfile
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".bmp")
        image.save(tmp.name)
        hPrinter = win32print.OpenPrinter(printer_name)
        try:
            win32print.StartDocPrinter(hPrinter, 1, ("Label", None, "RAW"))
            win32print.StartPagePrinter(hPrinter)
            with open(tmp.name, "rb") as f:
                win32print.WritePrinter(hPrinter, f.read())
            win32print.EndPagePrinter(hPrinter)
            win32print.EndDocPrinter(hPrinter)
        finally:
            win32print.ClosePrinter(hPrinter)
    elif platform.system() in ("Linux", "Darwin"):
        if not cups:
            raise RuntimeError("cups is required on this platform")
        conn = cups.Connection()
        import tempfile
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        image.save(tmp.name)
        conn.printFile(printer_name, tmp.name, "Label", {})
    else:
        raise RuntimeError("Unsupported OS or printing not configured")
