#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import pytest
from roast.utils import setup_logger, teardown_logger


@pytest.mark.freeze_time("2020-08-01 12:34:56")
def test_setup_logger_default(tmpdir, mocker):
    log_dirname = os.path.join(tmpdir, "log")
    setup_logger(log_dirname)
    teardown_logger()
    assert os.path.isfile(os.path.join(log_dirname, "20200801-123456.log"))

    datefmt = "%Y-%m-%d %H:%M"
    _logger = setup_logger(log_dirname, datefmt=datefmt)
    assert _logger.handlers[1].formatter.datefmt == datefmt


def test_setup_logger_dirname(tmpdir):
    log_dirname = os.path.join(tmpdir, "log")
    log_filename = "sometestfile.log"
    setup_logger(log_dirname, log_filename)
    teardown_logger()
    assert os.path.isfile(os.path.join(log_dirname, log_filename))
