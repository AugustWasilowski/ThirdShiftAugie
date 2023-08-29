import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)s [%(filename)s:%(lineno)d %(module)s:%(funcName)s()] - %(message)s')

def get_logger(name):
    return logging.getLogger(name)