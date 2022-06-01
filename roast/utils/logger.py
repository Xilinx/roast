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
    search_tokens=None,
    error_tokens=None,
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
        search_tokens=search_tokens,
        error_tokens=error_tokens,
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
        search_tokens=None,
        error_tokens=None,
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
            search_tokens (list): Tokens summary to add addition to Warning, Error, and Critical tokens.
            error_tokens (list): Error Tokens summary to add additional to the Warning, Error, and Critical tokens
            -- search_tokens and error_token are list of tokens which used for viewing
                the token summary in the respective logs files, it is not used for erroring out.

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
        self.time_format = time_format
        self.file_format = file_format
        self.fh.setFormatter(
            logging.Formatter(fmt=file_format, datefmt=time_format, style="{")
        )
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
        if search_tokens is None:
            search_tokens = []
        self.search_tokens = search_tokens

        if error_tokens is None:
            error_tokens = []
        self.error_tokens = error_tokens

    def write_summary(self):
        """
        Write log summary to the log file
        """

        self.fh.setFormatter(
            logging.Formatter(fmt="{message}", datefmt=self.time_format, style="{")
        )
        results = dict()
        builtin_tokens = ["WARNING", "ERROR", "CRITICAL"]
        tokens = builtin_tokens + self.search_tokens + self.error_tokens
        error_tokens = builtin_tokens + self.error_tokens
        for token in tokens:
            results[token] = []
        with open(self.log_path, "r") as f:
            for line in f:
                for token in tokens:
                    if re.search(rf"{token}", line):
                        results[token].append(line.strip())
        for token, lines in results.items():
            if lines:
                line_data = dict(Counter(lines))

                # Dump logs in logger file  and stdout
                self.logger.info(f"{token} Summary")
                for line, count in line_data.items():
                    self.logger.info(f"{count: >4} {line}")
                    print(f"{count: >4} {line}\n", file=sys.stdout)

                # Dump logs in error file
                if token in error_tokens:
                    print(f"{token} Summary", file=sys.stderr)
                    for line, count in line_data.items():
                        print(f"{count: >4} {line}", file=sys.stderr)

        self.fh.setFormatter(
            logging.Formatter(fmt=self.file_format, datefmt=self.time_format, style="{")
        )

    def close(self):
        if self.report_summary:
            self.write_summary()
        self.logger.removeHandler(self.fh)
        self.logger.removeHandler(self.out_h)
        self.logger.removeHandler(self.err_h)
        self.fh.close()
        self.out_h.close()
        self.err_h.close()
