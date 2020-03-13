import logging
from datetime import datetime
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get('timestamp'):
            now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            log_record['timestamp'] = now
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname

formatter = CustomJsonFormatter('(timestamp) (level) (name) (message)')

def get_logger(name: str = __name__, log_level: str = 'INFO') -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    if not [handler for handler in logger.handlers if handler.get_name() == 'json_handler']:
        logHandler = logging.StreamHandler()
        logHandler.set_name('json_handler')
        formatter = CustomJsonFormatter()
        logHandler.setFormatter(formatter)
        logger.addHandler(logHandler)
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