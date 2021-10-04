#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import logging
import filecmp
import pytest
from roast.utils import Logger, setup_logger, teardown_logger


@pytest.fixture(scope="function")
def teardown():
    yield
    teardown_logger()


@pytest.mark.freeze_time("2020-08-01 12:34:56")
def test_setup_logger_default(tmpdir, teardown):
    log_dirname = os.path.join(tmpdir, "log")
    logger = setup_logger(log_dirname)
    assert os.path.isfile(os.path.join(log_dirname, "20200801-123456.log"))
    assert logger.fh.level == logging.DEBUG
    assert logger.out_h.level == logging.INFO
    assert logger.err_h.level == logging.WARNING
    assert logger.fh.formatter._fmt == "{message}"
    assert logger.fh.formatter.datefmt == ""
    assert logger.out_h.formatter._fmt == "{message}"
    assert logger.out_h.formatter.datefmt == ""
    assert logger.err_h.formatter._fmt == "{message}"
    assert logger.err_h.formatter.datefmt == ""


def test_setup_logger_filename(tmpdir, teardown):
    log_dirname = os.path.join(tmpdir, "log")
    log_filename = "sometestfile.log"
    setup_logger(log_dirname, log_filename)
    assert os.path.isfile(os.path.join(log_dirname, log_filename))


def test_setup_logger_levels(tmpdir, teardown):
    log_dirname = os.path.join(tmpdir, "log")
    logger = setup_logger(
        log_dirname, console_level=logging.DEBUG, file_level=logging.INFO
    )
    assert logger.fh.level == logging.INFO
    assert logger.out_h.level == logging.DEBUG


def test_setup_logger_fmt(tmpdir, teardown):
    console_format = "{levelname} - {message}"
    file_format = "{asctime} - {levelname} - {message}"
    time_format = "%Y-%m-%d"
    log_dirname = os.path.join(tmpdir, "log")
    logger = setup_logger(
        log_dirname,
        console_format=console_format,
        file_format=file_format,
        time_format=time_format,
    )
    assert logger.fh.formatter._fmt == "{asctime} - {levelname} - {message}"
    assert logger.fh.formatter.datefmt == "%Y-%m-%d"
    assert logger.out_h.formatter._fmt == "{levelname} - {message}"
    assert logger.out_h.formatter.datefmt == "%Y-%m-%d"
    assert logger.err_h.formatter._fmt == "{levelname} - {message}"
    assert logger.err_h.formatter.datefmt == "%Y-%m-%d"


def test_logger(tmpdir):
    log = logging.getLogger("roast")
    log_dirname = os.path.join(tmpdir, "log")
    logger = Logger(
        log_dirname,
        console_level=logging.DEBUG,
        console_format="{levelname:<8} {message}",
        file_format="{levelname}: {message}",
        report_summary=True,
        report_tokens=["failed", "is.*error"],
    )
    log.info("this is an info test")
    log.debug("this is a debug test")
    log.warning("this is a warning test")
    log.error("this is an error")
    log.error("this is an error")
    log.error("this is another error")
    log.critical("this is critical")
    log.info("this is failed")
    logger.close()
    test_dir = os.path.dirname(__file__)
    assert filecmp.cmp(logger.log_path, os.path.join(test_dir, "summary_log.txt"))
