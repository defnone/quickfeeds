import logging
from logging.handlers import RotatingFileHandler


class IgnoreWaitressQueueWarnings(logging.Filter):
    def filter(self, record):
        if (
            record.levelname == "WARNING"
            and "waitress" in record.name
            and "Task queue depth is" in record.getMessage()
        ):
            return False
        return True


def setup_logging(log_level, log_file):
    logger = logging.getLogger()
    if not logger.handlers:
        waitress_warnings_filter = IgnoreWaitressQueueWarnings()

        handler = RotatingFileHandler(log_file, maxBytes=100000, backupCount=1)
        handler.setLevel(log_level)
        handler.addFilter(waitress_warnings_filter)

        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s - in %(pathname)s:%(lineno)d"
        )
        handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(waitress_warnings_filter)

        logger.setLevel(log_level)
        logger.addHandler(handler)
        logger.addHandler(console_handler)
