import os
import json
import logging
from logging.handlers import RotatingFileHandler


class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        level = record.levelname
        color = self.COLORS.get(level, "")
        record.levelname = f"{color}{level:<8}{self.RESET}" if color else f"{level:<8}"
        return super().format(record)


def _load_log_settings():
    """Read logger settings from config file, fallback to defaults."""
    defaults = {
        "level": "INFO",
        "file_path": "logs/corvus.log",
        "max_bytes": 1048576,  # 1 MB
        "backup_count": 5,
    }
    config_path = "config/config.json"
    if not os.path.exists(config_path):
        return defaults

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, json.JSONDecodeError):
        return defaults

    log_cfg = cfg.get("logger", {})
    level = str(log_cfg.get("level", cfg.get("log_level", defaults["level"]))).upper()
    file_path = str(log_cfg.get("file_path", defaults["file_path"]))
    max_bytes = int(log_cfg.get("max_bytes", defaults["max_bytes"]))
    backup_count = int(log_cfg.get("backup_count", defaults["backup_count"]))

    return {
        "level": level,
        "file_path": file_path,
        "max_bytes": max(1024, max_bytes),
        "backup_count": max(1, backup_count),
    }

def get_logger():
    """Returns the Corvus logger. Logs go to file only — never to the terminal."""
    os.makedirs("logs", exist_ok=True)
    settings = _load_log_settings()

    logger = logging.getLogger("corvus")
    logger.setLevel(getattr(logging, settings["level"], logging.INFO))
    logger.propagate = False

    if not logger.handlers:
        file_handler = RotatingFileHandler(
            settings["file_path"],
            maxBytes=settings["max_bytes"],
            backupCount=settings["backup_count"],
            encoding="utf-8",
        )
        clean_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(clean_formatter)
        logger.addHandler(file_handler)

    return logger