#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import logging
import socket
import pytest
from roast.xexpect import Xexpect


@pytest.fixture
def logger():
    return logging.getLogger("roast")


def test_xexpect_init(logger, mocker):
    mock_ssh_login = mocker.patch("roast.xexpect.ssh_login")
    Xexpect.sendline = mocker.Mock("sendline")
    Xexpect.expect = mocker.Mock("expect", return_value=3)
    x = Xexpect(logger)
    mock_ssh_login.assert_called_with(x)
    assert x.ip == socket.gethostname()
    assert x.prompt == x.ip
    assert Xexpect.sendline.call_count == 2

    x = Xexpect(logger, hostip="hostip")
    assert x.ip == "hostip"
    assert x.prompt == "(%|#|>|\\$|# )"

    mock_ssh_login_user = mocker.patch("roast.xexpect.ssh_login_user")
    x = Xexpect(logger, userid="user", password="password")
    mock_ssh_login_user.assert_called_with(x, "user", "password")
