"""Entry point for running the NiceGUI application."""

from app.main import main


if __name__ in {"__main__", "__mp_main__"}:  # pragma: no cover - manual start
    main()
