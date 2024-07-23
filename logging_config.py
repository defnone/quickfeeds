import logging
import os
from logging.handlers import TimedRotatingFileHandler


class IgnoreWaitressQueueWarnings(logging.Filter):
    """
    A custom logging filter that excludes specific warnings from
    the 'waitress' logging module.

    This filter is intended to suppress logs that are classified
    as warnings and contain the message "Task queue depth is".
    Such messages are often uninformative and by ignoring them,
    the overall log output is made more concise and focused on
    more relevant warnings. The filter checks the level of the
    log record, its originating module name, and the message
    content to decide whether to filter out the record.

    Attributes:
        record: The log record to evaluate for filtering.

    Methods:
        filter(record): Determines whether the specified log
        record should be passed through or filtered out based on
        its content.
    """

    def filter(self, record):
        if (
            record.levelname == "WARNING"
            and "waitress" in record.name
            and "Task queue depth is" in record.getMessage()
        ):
            return False
        return True


def setup_logging(log_level, log_file):
    """
    Configures logging for the application by setting up both a
    file handler and a console handler. This function creates a
    logger that formats log messages and manages warning filters
    effectively.

    Parameters:
        log_level (int): The logging level to set for the logger.
                         Common levels are DEBUG, INFO, WARNING,
                         ERROR, and CRITICAL.
        log_file (str): The path to the log file where log messages
                        will be stored. The log file will rotate
                        daily and keep a specified number of backup
                        files.

    Setup:
        - A custom formatter is defined to adjust the formatting
          of log messages.
        - A filter is applied to ignore specific warnings from
          the 'waitress' logging module.
        - A TimedRotatingFileHandler is created for logging to
          the specified log file.
        - A StreamHandler is created for logging messages to
          the console.

    The logging output includes:
        - Timestamp of the log entry.
        - Log level of the message (e.g., INFO, WARNING).
        - Actual log message.
        - Relative pathname and line number of the log entry.

    This configuration allows logging to a file and the console
    while filtering out certain unimportant warnings. It is
    primarily used for managing the application's logging in a
    more controlled manner and enhancing readability of output.
    """

    logger = logging.getLogger()
    if not logger.handlers:

        class CustomFormatter(logging.Formatter):
            """
            Custom formatter for logging that modifies the output
            to include a relative pathname for better readability.

            This formatter overrides the standard logging.Formatter
            to adjust the log message format, providing a clear
            structure that emphasizes key information such as the
            timestamp, log level, and message while also showing
            the relative file path and line number of the log entry.
            """

            def format(self, record):
                project_root = os.path.abspath(os.path.dirname(__file__))
                record.pathname = os.path.relpath(
                    record.pathname, project_root
                )

                return super().format(record)

        waitress_warnings_filter = IgnoreWaitressQueueWarnings()

        handler = TimedRotatingFileHandler(
            log_file, when="D", interval=3, backupCount=3
        )
        handler.setLevel(log_level)
        handler.addFilter(waitress_warnings_filter)

        formatter = CustomFormatter(
            "\033[36m%(asctime)s\033[0m \033[32m%(levelname)s\033[0m:   %(message)s   \033[37min %(pathname)s:%(lineno)d\033[0m",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(waitress_warnings_filter)

        logger.setLevel(log_level)
        logger.addHandler(handler)
        logger.addHandler(console_handler)
