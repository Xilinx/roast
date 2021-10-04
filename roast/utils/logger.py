#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import sys
import re
from datetime import datetime
import logging
from collections import Counter
from roast.utils import mkdir


def setup_logger(
    log_dirname,
    log_filename=None,
    console_level=logging.INFO,
    file_level=logging.DEBUG,
    console_format="",
    file_format="",
    time_format="",
    report_summary=False,
    report_tokens=None,
):
    global logger
    logger = Logger(
        log_dirname=log_dirname,
        log_filename=log_filename,
        console_level=console_level,
        file_level=file_level,
        console_format=console_format,
        file_format=file_format,
        time_format=time_format,
        report_summary=report_summary,
        report_tokens=report_tokens,
    )
    return logger


def teardown_logger():
    logger.close()


class Logger:
    def __init__(
        self,
        log_dirname,
        log_filename=None,
        console_level=logging.INFO,
        file_level=logging.DEBUG,
        console_format="",
        file_format="",
        time_format="",
        report_summary=False,
        report_tokens=None,
    ):
        """This defines two logging handlers - file at DEBUG level and console at INFO level.

        Args:
            log_dirname (str): Directory where log files will be written.
            log_filename (str, optional): Name for log file. If not specified,
                name will be generated based on timestamp. Defaults to None.
            console_level (int): Logging level for console. Defaults to logging.INFO or 20.
            file_level (int): Logging level for file. Defaults to logging.DEBUG or 10.
            console_format (str): Format in { style. Defaults to empty string which is {message}.
            file_format (str): Format in { style. Defaults to empty string which is {message}.
            time_format (str): Format in time.strftime(). Defaults to empty string which is %Y-%m-%d %H:%M:%S,uuu.
            report_summary (bool): Write summary to end of log file. Defaults to False,
            report_tokens (list): Tokens to summarize in addition to Warning, Error, and Critical.

        """

        mkdir(log_dirname)
        if log_filename is None:
            log_filename = datetime.now().strftime("%Y%m%d-%H%M%S") + ".log"
        self.log_path = os.path.join(log_dirname, log_filename)

        # Root logger
        self.logger = logging.getLogger("roast")
        self.logger.setLevel(logging.DEBUG)
        # File handler
        self.fh = logging.FileHandler(self.log_path)
        self.fh.setLevel(file_level)
        self.fh.setFormatter(logging.Formatter(file_format, time_format, "{"))
        self.logger.addHandler(self.fh)
        # stdout handler
        self.out_h = logging.StreamHandler(sys.stdout)
        self.out_h.setLevel(console_level)
        self.out_h.addFilter(lambda record: record.levelno <= logging.INFO)
        self.out_h.setFormatter(logging.Formatter(console_format, time_format, "{"))
        self.logger.addHandler(self.out_h)
        # stderr handler
        self.err_h = logging.StreamHandler(sys.stderr)
        self.err_h.setLevel(logging.WARNING)
        self.err_h.setFormatter(logging.Formatter(console_format, time_format, "{"))
        self.logger.addHandler(self.err_h)

        self.report_summary = report_summary
        if report_tokens is None:
            report_tokens = []
        self.report_tokens = report_tokens

    def write_summary(self):
        results = dict()
        tokens = ["WARNING", "ERROR", "CRITICAL"] + self.report_tokens
        for token in tokens:
            results[token] = []
        with open(self.log_path, "r") as f:
            for line in f:
                for token in tokens:
                    if re.search(fr"{token}", line):
                        results[token].append(line.strip())
        for token, lines in results.items():
            if lines:
                line_data = dict(Counter(lines))
                with open(self.log_path, "a") as f:
                    f.write(f"{token} Summary\n")
                    for line, count in line_data.items():
                        f.write(f"{count: >4} {line}\n")
                if token in ["WARNING", "ERROR", "CRITICAL"]:
                    print(f"{token} Summary", file=sys.stderr)
                    for line, count in line_data.items():
                        print(f"{count: >4} {line}", file=sys.stderr)

    def close(self):
        self.logger.removeHandler(self.fh)
        self.logger.removeHandler(self.out_h)
        self.logger.removeHandler(self.err_h)
        self.fh.close()
        self.out_h.close()
        self.err_h.close()
        if self.report_summary:
            self.write_summary()
