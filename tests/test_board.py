#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import socket
import pytest
from roast.component.board.board import Board


@pytest.fixture
def b():
    return Board(board_type="network_target")


def test_board_interface(b, mocker):
    assert isinstance(b, Board)
    assert b.driver.config == {}
    mock_start = mocker.patch.object(b, "start")
    mock_put = mocker.patch.object(b, "put")
    mock_get = mocker.patch.object(b, "get")
    mock_reset = mocker.patch.object(b, "reset")
    b.start()
    b.put("a", "b")
    b.get("c", "d")
    b.reset()
    mock_start.assert_called()
    mock_put.assert_called_once_with("a", "b")
    mock_get.assert_called_once_with("c", "d")
    mock_reset.assert_called()


def test_board_host_target(b, mocker):
    config = {"board_interface": "host_target"}
    b.driver.config = config
    mock_serial = mocker.patch(
        "roast.component.board.board.Serial", return_value=mocker.Mock("serial")
    )
    mock_serial.return_value.driver = mocker.Mock("driver", return_value="driver")
    mock_serial.return_value.driver.exit = mocker.Mock("exit")
    mock_relay = mocker.patch(
        "roast.component.board.board.Relay", return_value=mocker.Mock("relay")
    )
    mock_relay.return_value.driver = mocker.Mock("driver", return_value="driver")
    mock_relay.return_value.driver.reconnect = mocker.Mock("reconnect")
    mock_xexpect = mocker.patch(
        "roast.component.board.board.Xexpect", return_value="xexpect"
    )
    mock_xsdb = mocker.patch("roast.component.board.board.Xsdb", return_value="xsdb")
    b.start()
    mock_serial.assert_called()
    mock_relay.assert_called()
    assert b.driver.host_console == "xexpect"
    assert b.driver.xsdb == "xsdb"
    assert b.driver.host == socket.gethostname()

    config = {
        "board_interface": "host_target",
        "relay_type": "None",
        "remote_host": "host",
    }
    b.driver.config = config
    b.driver.reboot = True
    b.start()
    mock_serial.return_value.driver.exit.assert_called()
    mock_relay.return_value.driver.reconnect.assert_called()
    assert b.driver.host == "host"


def test_board_network_target(b, mocker):
    config = {
        "board_interface": "network_target",
        "relay_type": "None",
        "target_ip": "target_ip",
        "user": "user",
        "password": "password",
    }
    b.driver.config = config
    mock_xexpect = mocker.patch(
        "roast.component.board.board.Xexpect", return_value="xexpect"
    )
    b.start()
    assert b.driver.target_console == "xexpect"
    assert b.driver.ip == "target_ip"
    assert b.driver.user == "user"
    assert b.driver.password == "password"


def test_board_qemu(b, mocker):
    config = {"board_interface": "qemu"}
    b.driver.config = config
    mock_log = mocker.patch(
        "roast.component.board.board.log", return_value=mocker.Mock("log")
    )
    mock_log.return_value.info = mocker.Mock("info")
    b.start()
    assert b.driver.interface == "qemu"


def test_board_put(b, mocker):
    b.driver.interface = "host_target"
    b.driver.host_console = "host_console"
    b.driver.host = "host"
    b.driver.serial = mocker.Mock("serial")
    b.driver.serial.sendline = mocker.Mock("sendline")
    b.driver.serial.expect = mocker.Mock("expect")
    b.driver.serial.search = mocker.Mock("search", return_value="target_ip")
    mock_scp = mocker.patch("roast.component.board.board.scp_file_transfer")
    b.put("a", "b")
    mock_scp.assert_called_once_with(
        "host_console", "a", "b", proxy_server="host", target_ip="target_ip"
    )


def test_board_get(b, mocker):
    b.driver.interface = "host_target"
    b.driver.host_console = "host_console"
    b.driver.host = "host"
    b.driver.serial = mocker.Mock("serial")
    b.driver.serial.sendline = mocker.Mock("sendline")
    b.driver.serial.expect = mocker.Mock("expect")
    b.driver.serial.search = mocker.Mock("search", return_value="target_ip")
    mock_scp = mocker.patch("roast.component.board.board.scp_file_transfer")
    b.get("a", "b")
    mock_scp.assert_called_once_with(
        "host_console",
        "a",
        host_path="b",
        transfer_to_target=False,
        target_ip="target_ip",
        proxy_server="host",
    )


def test_board_reset(b, mocker):
    b.driver.isLive = True
    b.driver.interface = "host_target"
    b.driver.relay = mocker.Mock("relay")
    b.driver.relay.reconnect = mocker.Mock("reconnect")
    b.reset()
    b.driver.relay.reconnect.assert_called_once()


def test_board_start_exception(b):
    config = {"board_interface": "None"}
    b.driver.config = config
    with pytest.raises(Exception):
        b.start()
