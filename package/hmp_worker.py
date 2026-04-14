#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2021, The CBM-STS Project"
__date__       = "2025-05-01"
__version__    = "3.0.0"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

import sys, time

### loguru
###
from loguru import logger as log_hmp_worker

log_hmp_worker.remove()

myformat =  "<green>{time:HH:mm:ss}</green> | "\
            "<level>{level: <8}</level> | "\
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "\
            "{message}"

log_hmp_worker.add( sys.stdout, 
                    level="DEBUG",
                    # level="INFO",
                    # level="WARNING",
                    # level="ERROR",
                    # level="CRITICAL", 
                    format=myformat) #add a new handler which has INFO as the default


from PyQt6.QtCore import QObject, QRunnable, QThread, pyqtSignal

###############################################################################
class HmpWorkerSignals(QObject):
    hmpSignal = pyqtSignal(list)  # Signal to update progress as a string

###############################################################################
class HmpWorker(QRunnable):
    """
    Worker thread that performs a task in the background.
    """
    def __init__(self, hmp4040):
        super(HmpWorker, self).__init__()

        self.signals        = HmpWorkerSignals()
        self.is_interrupted = False
        self.hmp4040        = hmp4040
        self.values         = [None] * 13
        self.list_of_channels = [1, 2, 3, 4]
        log_hmp_worker.debug(f"HmpWorker created")

    #==========================================================================
    def run(self):
        while True:
            if self.is_interrupted:
                break
            self.values = self.hmp4040.meas_all(self.list_of_channels) + self.hmp4040.ch_states(self.list_of_channels)
            self.values.append(time.time())
            self.signals.hmpSignal.emit(self.values)
            # log_hmp_worker.debug(f"{self.values}")
            QThread.msleep(10)

    #==========================================================================
    def stop(self):
        log_hmp_worker.debug("HmpWorker.stop()")
        self.is_interrupted = True
