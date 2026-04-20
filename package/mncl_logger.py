#!/usr/bin/env python3

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2026, The Super FRS Project"
__version__    = "1.0.0"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

import sys
from loguru import logger

# class MnclLogger:

#     def __init__(self, 
#                  test_log_file: str = "logs/tamex_manager.log",
#                  debug_log_file: str = "logs/debug_tamex_manager.log"):

#         self.test_log_file  = test_log_file
#         self.debug_log_file = debug_log_file

#==========================================================================
def setup_logger(test_log_file: str = None, debug_log_file: str = None):
    logger.remove() #remove the old handler.

    logger.add( sys.stdout, 
                level = "INFO",
                format = "{time:HH:mm:ss}|{level: >8}| {message}")

    log_fmt =   "<green>{time:YY-MM-DD HH:mm:ss}</green> | "\
                "<level>{level: <8}</level> | "\
                "<magenta>{module}</magenta>:<cyan>{function}</cyan>:"\
                "<yellow>{line}</yellow> - <level>{message}</level>"

    ## for quasi-permanent log file
    logger.add( debug_log_file,
                level       = "DEBUG",
                mode        = "a", 
                format      = log_fmt,
                rotation    = "50 MB",   # rotate after
                retention   = "3 month", # keep logs for
                compression = "zip")     # compress rotated logs

    ## for test log file
    logger.add( test_log_file,
                mode="w",
                level = "DEBUG",
                format = "<green>{time:YY-MM-DD HH:mm:ss}</green> | "\
                        "<level>{level: <8}</level> | "\
                        "<magenta>{module}</magenta>:<cyan>{function}</cyan>:"\
                        "<yellow>{line}</yellow> - <level>{message}</level>")
    
    logger.success(f"MnclLogger initialized with test log: {test_log_file} and debug log: {debug_log_file}")
