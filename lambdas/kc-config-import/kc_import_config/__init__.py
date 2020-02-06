import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
from .cp_config_import import handler as cp_handler