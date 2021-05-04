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
    console_fmt={},
    file_fmt={},
    **kwargs,
):
    """This defines two logging handlers - file at DEBUG level and console at INFO level.
    If any keyword arguments are provided, all other parameters will be discarded with both
    handlers set to the same format.

    The dictionaries for console_fmt and file_fmt are in the format:
    {"fmt": <format string>, "datefmt": <format string>, "style': <format string>}

    Args:
        log_dirname (str): Directory where log files will be written.
        log_filename (str, optional): Name for log file. If not specified,
            name will be generated based on timestamp. Defaults to None.
        console_level (int): Logging level for console. Defaults to logging.INFO or 20.
        file_level (int): Logging level for file. Default to logging.DEBUG or 10.
        console_fmt (dict): Dictionary of formatting parameters.
        file_fmt (dict): Dictionary of file parameters.
        **fmt (str): Message format.
        **datefmt (str): Date format.
        **style (str): Style format.

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

    file_formatter = logging.Formatter()
    console_formatter = logging.Formatter()
    if file_fmt:
        fmt = file_fmt.get("fmt")
        datefmt = file_fmt.get("datefmt")
        style = file_fmt.get("style", "%")
        file_formatter = logging.Formatter(fmt, datefmt, style)
    if console_fmt:
        fmt = console_fmt.get("fmt")
        datefmt = console_fmt.get("datefmt")
        style = console_fmt.get("style", "%")
        console_formatter = logging.Formatter(fmt, datefmt, style)
    if kwargs:
        file_formatter = logging.Formatter(**kwargs)
        console_formatter = logging.Formatter(**kwargs)
    fh.setFormatter(file_formatter)
    ch.setFormatter(console_formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


def teardown_logger():
    logger.removeHandler(fh)
    logger.removeHandler(ch)
    fh.close()
    ch.close()
