"""Helpers for listing printers and printing images across platforms."""

import platform
from typing import List
from PIL import Image


if platform.system() == 'Windows':
    import win32print
elif platform.system() in ('Linux', 'Darwin'):
    import cups
else:
    win32print = None
    cups = None


def list_printers() -> List[str]:
    """Return a list of available printer names."""

    if platform.system() == 'Windows' and win32print:
        return [p[2] for p in win32print.EnumPrinters(2)]
    elif platform.system() in ('Linux', 'Darwin') and cups:
        conn = cups.Connection()
        return list(conn.getPrinters().keys())
    return []


def print_label(image: Image.Image, printer_name: str) -> None:
    """Send the given image to ``printer_name``.

    The implementation handles Windows and CUPS based systems. For other
    platforms a ``RuntimeError`` is raised.
    """

    if platform.system() == 'Windows' and win32print:
        import tempfile
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.bmp')
        image.save(tmp.name)
        hPrinter = win32print.OpenPrinter(printer_name)
        try:
            hJob = win32print.StartDocPrinter(hPrinter, 1, ('Label', None, 'RAW'))
            win32print.StartPagePrinter(hPrinter)
            with open(tmp.name, 'rb') as f:
                win32print.WritePrinter(hPrinter, f.read())
            win32print.EndPagePrinter(hPrinter)
            win32print.EndDocPrinter(hPrinter)
        finally:
            win32print.ClosePrinter(hPrinter)
    elif platform.system() in ('Linux', 'Darwin') and cups:
        conn = cups.Connection()
        import tempfile
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        image.save(tmp.name)
        conn.printFile(printer_name, tmp.name, 'Label', {})
    else:
        raise RuntimeError('Unsupported OS or printing not configured')
