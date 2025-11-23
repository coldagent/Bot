"""Shared logging setup for the bot and cogs.

Call `setup_logging()` early (for example from `bot.py`), or import and call
from individual cogs if you want to ensure setup on import. The function is
idempotent (it clears handlers first) so calling multiple times is safe.
"""
from __future__ import annotations

import logging
import colorlog
import colorama


def setup_logging(level: int = logging.INFO) -> None:
    """Configure colored logging for console.

    - Clears existing handlers on the root logger.
    - Adds a single StreamHandler to the root logger.
    - Prevents log propagation from known verbose/duplicating libraries.
    """
    # Make idempotent: remove any existing handlers from the root logger
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)

    # Initialize colorama (Windows) - keep this for cross-platform color support
    colorama.init()

    # Custom formatter class (as you defined it)
    class CustomColoredFormatter(colorlog.ColoredFormatter):
        def format(self, record: logging.LogRecord) -> str:
            # Ensure asctime exists and wrap it in gray + bold
            record.asctime = self.formatTime(record, self.datefmt)
            record.asctime = f"\033[1;90m{record.asctime}\033[0m"

            # Color the logger name pink (magenta)
            record.name = f"\033[95m{record.name}\033[0m"

            return super().format(record)

    formatter = CustomColoredFormatter(
        fmt="%(asctime)s %(log_color)s%(levelname)-8s%(reset)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "green",
            "INFO": "blue",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )

    # Console handler (defined once)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Configure root logger (The SINGLE point of output)
    root.setLevel(level)
    root.addHandler(console_handler)

    logging.getLogger("discord").propagate = False
    logging.getLogger("discord").setLevel(logging.INFO) # Set the minimum level you want to see
    
    logging.getLogger("websockets").propagate = False
    logging.getLogger("websockets").setLevel(logging.WARNING)

    logging.getLogger("asyncio").propagate = False
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    logging.getLogger("urllib3").propagate = False
    logging.getLogger("urllib3").setLevel(logging.WARNING)
