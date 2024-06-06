import os
import logging
from logging_config import setup_logging


setup_logging(
    os.getenv("LOG_LEVEL", "DEBUG"), os.getenv("LOG_FILE", "logs/app.log")
)
logger = logging.getLogger(__name__)


def secret_key():
    secret_key_file = "secret_key"
    if os.path.isfile(secret_key_file):
        with open(secret_key_file, "r", encoding="utf-8") as f:
            sk = f.read().strip()
            logger.info("Secret key loaded from file.")
    else:
        sk = os.urandom(24).hex()
        with open(secret_key_file, "w", encoding="utf-8") as f:
            f.write(sk)
            logger.info("New secret key generated and saved to file.")

    return sk
