#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import pytest
from datetime import datetime
import logging

from roast.component.hwflow import HwbuildRunner
from roast.utils.logger import setup_logger
from roast.utils.roast_utils import reset


def test_hwflow_versal_3bram(request, create_configuration):
    config = create_configuration()
    build_dir = os.path.abspath(config["buildDir"])
    log_dir = os.path.join(build_dir, "hwflow_debug_logs")
    log_filename = (
        "test_hwflow_versal_3bram_" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".log"
    )
    setup_logger(log_dir, log_filename=log_filename)
    log = logging.getLogger("roast")
    log.debug(f"log @: {log_dir}/{log_filename}")
    build_dir = os.path.join(build_dir, "test_hwflow_versal_3bram")
    config["buildDir"] = build_dir
    reset(build_dir)
    hw = HwbuildRunner(config)
    hw.configure()
    hw.createhw()
    assert hw.deploy() == True
