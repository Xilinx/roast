#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import socket
import pytest
from roast.serial import Serial
from roast.utils import register_plugin


config = {
    "board_interface": "host_target",
    "remote_host": "remote_host",
    "com": "com",
    "baudrate": "baudrate",
}


@pytest.fixture
def s():
    name = "dummy_serial"
    register_plugin(name, "serial", "tests.test_plugin:DummySerial")
    return Serial(serial_type=name, config=config)


def test_serial_interface(s, mocker):
    assert isinstance(s, Serial)
    assert s.driver.config == config
    s.exit()
    assert s.driver.exit == True
