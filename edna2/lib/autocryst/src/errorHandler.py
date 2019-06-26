"""
Created on 18-Feb-2019
Author: S. Basu
"""

import logging
import graypy


def add_gray_handler(loggername):
    logger = logging.getLogger(loggername)
    logger.setLevel(logging.DEBUG)

    handler = graypy.GELFHandler('graylog-dau.esrf.fr', 12206)
    logger.addHandler(handler)

    logger.debug('Message:{}'.format('Gray Logger is running for esrf'))

    return logger


if __name__ == '__main__':
    pass
