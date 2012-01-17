from PyQt4.QtCore import *

import logging

class Console(QObject):
    """
    Makes it possible to use a Python logger from javascript.
    """
    def __init__(self, logger=None, parent=None):
        super(Console, self).__init__(parent)
        if not logger:
            logger = logging.getLogger()
        self.logger = logger

    @pyqtSlot(str)
    def debug(self, msg):
        self.logger.debug(msg)

    @pyqtSlot(str)
    def info(self, msg):
        self.logger.info(msg)

    @pyqtSlot(str)
    def warning(self, msg):
        self.logger.warning(msg)

    @pyqtSlot(str)
    def error(self, msg):
        self.logger.error(msg)

    @pyqtSlot(str)
    def critical(self, msg):
        self.logger.critical(msg)
