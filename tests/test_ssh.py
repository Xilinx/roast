#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import socket
import logging
import pexpect
from pexpect import pxssh
import pytest
from unittest.mock import call
from roast.ssh import ssh_login, ssh_login_user, pxssh_login


@pytest.fixture
def c(mocker):
    c = mocker.Mock("c")
    c.hostname = socket.gethostname()
    c.ip = c.hostname
    c.non_interactive = True
    c.echo = False
    c.runcmd = mocker.Mock("runcmd")
    return c


def test_ssh_login(c, mocker):
    mock_spawn = mocker.patch.object(pexpect, "spawn")
    mock_spawn.return_value = mocker.Mock("spawn")
    mock_spawn.return_value.expect = mocker.Mock("expect", return_value=2)
    mock_spawn.return_value.sendline = mocker.Mock("sendline")
    ssh_login(c)
    mock_spawn.assert_called_with(
        "/bin/bash --norc", codec_errors="replace", echo=False, encoding="utf-8"
    )
    mock_spawn.return_value.sendline.assert_called_with("bash --norc | cat")
    c.non_interactive = False
    ssh_login(c)
    mock_spawn.return_value.sendline.assert_called_with("bash --norc")
    c.runcmd.assert_called_with(r"PS1='\u@\H:\t:\w\$ '", expected=socket.gethostname())
    c.hostname = "hostname"
    c.ip = c.hostname
    c.cmd = "cmd"
    ssh_login(c)
    mock_spawn.assert_called_with(
        "cmd hostname '/bin/bash --norc'",
        codec_errors="replace",
        echo=False,
        encoding="utf-8",
    )


def test_ssh_login_exception(c, mocker):
    mock_spawn = mocker.patch.object(pexpect, "spawn")
    mock_spawn.return_value = mocker.Mock("spawn")
    mock_spawn.return_value.expect = mocker.Mock("expect", return_value=3)
    with pytest.raises(Exception, match="ssh"):
        ssh_login(c)


def test_ssh_login_user(c, mocker):
    mocker.patch("time.sleep")
    mocker.patch("sys.exit")
    mock_spawn = mocker.patch.object(pexpect, "spawn")
    mock_spawn.return_value = mocker.Mock("spawn")
    mock_spawn.return_value.expect = mocker.Mock("expect", return_value=4)
    mock_spawn.return_value.sendline = mocker.Mock("sendline")
    ssh_login_user(c, "user", "password")
    mock_spawn.assert_called_with(
        f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null user@{socket.gethostname()} -y",
        codec_errors="replace",
        echo=False,
        encoding="utf-8",
    )

    mock_error = mocker.patch("roast.ssh.log.error")
    mock_spawn.return_value.expect = mocker.Mock("expect", return_value=3)
    mock_spawn.return_value.sendline = mocker.Mock("sendline")
    ssh_login_user(c, "user", "password")
    mock_spawn.return_value.sendline.assert_called_with("/bin/bash --norc")
    mock_error.assert_called_with(
        f"Error: Failed to establish ssh connection on {socket.gethostname()} with username:user password:password"
    )

    call_password = call("password")
    call_bash = call("/bin/bash --norc")

    mock_spawn.return_value.expect = mocker.Mock("expect", return_value=2)
    mock_spawn.return_value.sendline = mocker.Mock("sendline")
    ssh_login_user(c, "user", "password")
    mock_spawn.return_value.sendline.assert_has_calls(
        [call_password, call_password, call_password, call_password, call_bash]
    )

    mock_spawn.return_value.expect = mocker.Mock("expect", return_value=1)
    ssh_login_user(c, "user", "password")
    mock_error.call_count == 5
    mock_spawn.return_value.sendline.assert_has_calls(
        [call_password, call_password, call_password, call_password, call_bash]
    )

    mock_spawn.return_value.expect = mocker.Mock("expect", return_value=10)
    ssh_login_user(c, "user", "password")
    mock_spawn.return_value.sendline.assert_has_calls(
        [call_password, call_password, call_password, call_password, call_bash]
    )


def test_pxssh_login(c, mocker):
    mock_pxssh = mocker.patch.object(pxssh, "pxssh", return_value=mocker.Mock("pxssh"))
    mock_pxssh.return_value.login = mocker.Mock("login")
    pxssh_login(c, "user", "password")
    mock_pxssh.return_value.login.assert_called_with(
        socket.gethostname(), "user", "password"
    )

    mocker.patch("sys.exit")
    mocker.patch("time.sleep")
    mock_pxssh = mocker.patch.object(
        pxssh, "pxssh", side_effect=pxssh.ExceptionPxssh("ERROR")
    )
    mock_error = mocker.patch("roast.ssh.log.error")
    pxssh_login(c, "user", "password")
    mock_error.assert_called_with(
        f"error: Failed to establish ssh connection with {socket.gethostname()}!"
    )
