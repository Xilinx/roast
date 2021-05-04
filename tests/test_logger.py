#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import logging
import pytest
from roast.utils import setup_logger, teardown_logger


@pytest.fixture(scope="function")
def teardown():
    yield
    teardown_logger()


@pytest.mark.freeze_time("2020-08-01 12:34:56")
def test_setup_logger_default(tmpdir, teardown):
    log_dirname = os.path.join(tmpdir, "log")
    _logger = setup_logger(log_dirname)
    assert os.path.isfile(os.path.join(log_dirname, "20200801-123456.log"))
    fh = _logger.handlers[1]
    ch = _logger.handlers[2]
    assert fh.level == logging.DEBUG
    assert ch.level == logging.INFO
    formatter = logging.Formatter()
    assert fh.formatter._fmt == formatter._fmt
    assert fh.formatter.datefmt == formatter.datefmt
    assert ch.formatter._fmt == formatter._fmt
    assert ch.formatter.datefmt == formatter.datefmt


def test_setup_logger_filename(tmpdir, teardown):
    log_dirname = os.path.join(tmpdir, "log")
    log_filename = "sometestfile.log"
    setup_logger(log_dirname, log_filename)
    assert os.path.isfile(os.path.join(log_dirname, log_filename))


def test_setup_logger_levels(tmpdir, teardown):
    log_dirname = os.path.join(tmpdir, "log")
    _logger = setup_logger(
        log_dirname, console_level=logging.DEBUG, file_level=logging.INFO
    )
    fh = _logger.handlers[1]
    ch = _logger.handlers[2]
    assert fh.level == logging.INFO
    assert ch.level == logging.DEBUG


def test_setup_logger_kwargs(tmpdir, teardown):
    fmt = "%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s"
    datefmt = "%Y-%m-%d"
    log_dirname = os.path.join(tmpdir, "log")
    _logger = setup_logger(log_dirname, fmt=fmt, datefmt=datefmt)
    fh = _logger.handlers[1]
    ch = _logger.handlers[2]
    assert fh.formatter._fmt == fmt
    assert fh.formatter.datefmt == datefmt
    assert ch.formatter._fmt == fmt
    assert ch.formatter.datefmt == datefmt


def test_setup_logger_fmt(tmpdir, teardown):
    console_fmt = {"fmt": "%(levelname)s - %(message)s", "datefmt": "%Y-%m-%d"}
    file_fmt = {"fmt": "{levelname} - {message}", "datefmt": "%Y-%m", "style": "{"}
    log_dirname = os.path.join(tmpdir, "log")
    _logger = setup_logger(log_dirname, console_fmt=console_fmt, file_fmt=file_fmt)
    fh = _logger.handlers[1]
    ch = _logger.handlers[2]
    assert fh.formatter._fmt == file_fmt["fmt"]
    assert fh.formatter.datefmt == file_fmt["datefmt"]
    assert ch.formatter._fmt == console_fmt["fmt"]
    assert ch.formatter.datefmt == console_fmt["datefmt"]
