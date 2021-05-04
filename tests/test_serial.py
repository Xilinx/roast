#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import pytest
from roast.serial import Serial
from roast.utils import register_plugin


config = {
    "board_interface": "host_target",
    "remote_host": "remote_host",
    "hostname": "hostname",
    "com": "com",
    "baudrate": "baudrate",
}


def test_serial_interface(mocker):
    name = "dummy_serial"
    register_plugin(name, "serial", "test_plugin:DummySerial")
    mock_xexpect = mocker.patch(
        "roast.serial.Xexpect", return_value=mocker.Mock("xexpect")
    )
    mock_xexpect.return_value.expect = mocker.Mock("xexpect", return_value="xexpect")
    mock_xexpect.return_value.sendline = mocker.Mock("sendline")
    mock_xexpect.return_value.runcmd = mocker.Mock("runcmd")
    mock_xexpect.return_value.runcmd_list = mocker.Mock("runcmd_list")
    mock_xexpect.return_value.sendcontrol = mocker.Mock("sendcontrol")
    mock_xexpect.return_value.send = mocker.Mock("send")
    mock_xexpect.return_value.output = mocker.Mock("output")
    mock_xexpect.return_value._setup_init = mocker.Mock("setup_init")
    mock_xexpect.return_value.search = mocker.Mock("search")
    mock_xexpect.return_value.sync = mocker.Mock("sync")
    s = Serial(serial_type="dummy_serial", config=config)
    assert isinstance(s, Serial)
    assert s.driver.config == config
    assert s.driver.hostname == "hostname"
    assert s.driver.configure == True
    assert s.driver.connect == True
    s.driver.prompt = "prompt"
    assert s.driver.prompt == "prompt"
    s.exit()
    assert s.driver.exit == True


def test_serial_exception():
    with pytest.raises(Exception, match="No 'roast.serial' driver found"):
        Serial(serial_type="", config=config)
