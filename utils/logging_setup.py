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
    """Configure colored logging for console and make it idempotent.

    - Initializes `colorama` for Windows support
    - Clears existing handlers on the root logger
    - Adds a single StreamHandler with colorized formatter
    - Attaches the same handler to `discord` logger and disables propagation
    """
    # Make idempotent: remove any existing handlers from the root logger
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)

    # Initialize colorama (Windows)
    colorama.init()

    # Custom formatter: bold timestamp, bold levelname (color applied via %(log_color)s), pink logger name
    class CustomColoredFormatter(colorlog.ColoredFormatter):
        def format(self, record: logging.LogRecord) -> str:
            # Ensure asctime exists and wrap it in gray + bold
            record.asctime = self.formatTime(record, self.datefmt)
            record.asctime = f"\033[1;90m{record.asctime}\033[0m"

            # Bold the levelname (color will be applied via %(log_color)s prefix)
            record.levelname = f"\033[1m{record.levelname}\033[0m"

            # Color the logger name pink (magenta)
            record.name = f"\033[95m{record.name}\033[0m"

            return super().format(record)

    formatter = CustomColoredFormatter(
        fmt="%(asctime)s %(log_color)s%(levelname)-8s%(reset)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Configure root logger
    root.setLevel(level)
    root.addHandler(console_handler)

    # Configure discord loggers: attach handler and prevent propagation to root
    discord_logger = logging.getLogger("discord")
    discord_logger.setLevel(level)
    discord_logger.propagate = False
    # avoid adding duplicate handlers
    if not any(isinstance(h, type(console_handler)) for h in discord_logger.handlers):
        discord_logger.addHandler(console_handler)

    # Reduce very noisy sub-loggers
    logging.getLogger("discord.http").setLevel(logging.WARNING)
    logging.getLogger("discord.gateway").setLevel(logging.INFO)
