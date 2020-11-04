#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import socket
import pytest
from roast.serial import Serial


config = {
    "board_interface": "host_target",
    "remote_host": "remote_host",
    "com": "com",
    "baudrate": "baudrate",
}


def test_serial_interface(mocker):
    mock_init = mocker.patch("roast.serial.HostSerial.__init__", return_value=None)
    s = Serial(serial_type="host", config=config)
    assert isinstance(s, Serial)
    mock_init.assert_called_with(config)


def test_serial(mocker):
    mock_xexpect = mocker.patch(
        "roast.serial.Xexpect", return_value=mocker.Mock("xexpect")
    )
    mock_xexpect.return_value.expect = mocker.Mock("xexpect", return_value="xexpect")
    mock_xexpect.return_value.sendline = mocker.Mock("sendline")
    mock_xexpect.return_value.runcmd = mocker.Mock("runcmd")
    mock_xexpect.return_value.runcmd_list = mocker.Mock("runcmd_list")
    mock_xexpect.return_value.sendcontrol = mocker.Mock("sendcontrol")
    mock_xexpect.return_value.output = mocker.Mock("output")
    mock_xexpect.return_value.send = mocker.Mock("send")
    mock_xexpect.return_value.search = mocker.Mock("search")
    mock_xexpect.return_value._setup_init = mocker.Mock("setup_init")
    mock_xexpect.return_value.sync = mocker.Mock("sync")
    mock_picom_connect = mocker.patch("roast.serial.picom_connect")
    mock_picom_disconnect = mocker.patch("roast.serial.picom_disconnect")
    s = Serial(serial_type="host", config=config)
    assert s.driver.config == config
    assert s.driver.hostname == "remote_host"
    mock_picom_connect.assert_called_with(mocker.ANY, "com", "baudrate")

    s = Serial(serial_type="host", config=config)
    s.exit()
    mock_picom_disconnect.assert_called()


def test_serial_exception():
    config["board_interface"] = None
    with pytest.raises(Exception, match="invalid serial interface"):
        Serial(serial_type="host", config=config)
