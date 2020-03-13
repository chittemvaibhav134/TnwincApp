import logging
from datetime import datetime

def get_logger(name: str = __name__, log_level: str = 'INFO') -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    # This can't possibly be the correct way to solve this problem.. but
    # i'm hacking this in so that log statements are actually printed when testing
    # in the repl. The bonus if condition is so that they are only displayed once...
    if __name__ == '__main__':
        from sys import stdout
        if not [handler for handler in logger.handlers if handler.get_name() == 'stdout_for_repl']:
            stream = logging.StreamHandler(stdout)
            stream.set_name('stdout_for_repl')
            logger.addHandler(stream)
    return logger