#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
from datetime import datetime
import logging
from roast.utils import mkdir


def setup_logger(
    log_dirname,
    log_filename=None,
    console_level=logging.INFO,
    file_level=logging.DEBUG,
    **kwargs,
):
    """This defines two logging handlers - file at DEBUG level and console at INFO level.
    Any keyword arguments will be passed to logging.Formatter.

    Args:
        log_dirname (str): Directory where log files will be written.
        log_filename (str, optional): Name for log file. If not specified,
            name will be generated based on timestamp. Defaults to None.
    """
    mkdir(log_dirname)
    if log_filename is None:
        log_filename = datetime.now().strftime("%Y%m%d-%H%M%S") + ".log"
    log_path = os.path.join(log_dirname, log_filename)

    global logger, fh, ch
    logger = logging.getLogger("roast")
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_path)
    fh.setLevel(file_level)
    ch = logging.StreamHandler()
    ch.setLevel(console_level)
    if kwargs:
        formatter = logging.Formatter(**kwargs)
    else:
        formatter = logging.Formatter(
            "%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


def teardown_logger():
    logger.removeHandler(fh)
    logger.removeHandler(ch)
    fh.close()
    ch.close()
