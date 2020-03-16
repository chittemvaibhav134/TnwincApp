import logging

def get_logger(name: str = __name__, log_level: str = 'INFO') -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    return logger