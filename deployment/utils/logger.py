import logging

APP_VERSION = "0.0.1"
LOG_LEVEL = logging.INFO
LOG_CONFIG = (
    f"AroTranslate {APP_VERSION}: "
    + " [%(levelname)s] %(asctime)s %(name)s:%(lineno)d - %(message)s"
)

def configure_logging():
    logging.basicConfig(level=LOG_LEVEL, format=LOG_CONFIG)
    logger = logging.getLogger(__name__)
    logger.info("Logger configured successfully.")

