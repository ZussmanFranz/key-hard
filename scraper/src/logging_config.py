import logging
import logging.config
import colorlog
import json

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage()
        }
        return json.dumps(log_record)

def setup_logging():
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            # 1. The Colored Formatter (For Console)
            "colored": {
                "()": "colorlog.ColoredFormatter",
                "format": "%(log_color)s%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%H:%M:%S",
                "log_colors": {
                    "DEBUG": "cyan",
                    "INFO": "white",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "black,bg_red",
                },
                "secondary_log_colors": {},
                "style": "%"
            },
            # 2. The Clean Formatter (For Files/Production)
            "json": {
                "()": JsonFormatter,
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "colored",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": "app.log",
                "maxBytes": 10485760,
                "backupCount": 5
            }
        },
        "loggers": {
            "": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": True
            }
        }
    }

    logging.config.dictConfig(logging_config)

if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger("my_app")

    logger.debug("This is a debug message (Cyan)")
    logger.info("System is running normally (White)")
    logger.warning("Disk space is getting low (Yellow)")
    logger.error("Database connection failed (Red)")
    logger.critical("SYSTEM SHUTDOWN IMMINENT (Red Background)")