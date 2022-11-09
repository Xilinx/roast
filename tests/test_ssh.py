#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import socket
import logging
import pexpect
from pexpect import pxssh
import pytest
from roast.ssh import ssh_login, ssh_login_user, pxssh_login, scp_file_transfer


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
    mock_spawn = mocker.patch.object(pexpect, "spawn")
    mock_spawn.return_value = mocker.Mock("spawn")
    mock_spawn.return_value.expect = mocker.Mock("expect", return_value=4)
    mock_spawn.return_value.sendline = mocker.Mock("sendline")
    call_expect_ssh = mocker.call(
        [
            pexpect.EOF,
            pexpect.TIMEOUT,
            "password:",
            "Permission denied",
            "(%|#|>|\\$|# )",
        ],
        timeout=60,
    )
    call_expect_bash = mocker.call("bash-", timeout=60)

    ssh_login_user(c, "user", "password")
    mock_spawn.assert_called_with(
        f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null user@{socket.gethostname()} -y",
        codec_errors="replace",
        echo=False,
        encoding="utf-8",
    )
    mock_spawn.return_value.sendline.assert_called_with("/bin/bash --norc")
    mock_spawn.return_value.expect.assert_has_calls([call_expect_ssh, call_expect_bash])

    call_sendline_bash = mocker.call("/bin/bash --norc")
    call_sendline_password = mocker.call("password")
    mock_spawn.return_value.expect = mocker.Mock("expect")
    mock_spawn.return_value.expect.side_effect = [2, 4, None]
    ssh_login_user(c, "user", "password")
    mock_spawn.return_value.sendline.assert_has_calls(
        [call_sendline_bash, call_sendline_password, call_sendline_bash]
    )


def test_ssh_login_user_exception(c, mocker):
    mocker.patch("time.sleep")
    mock_spawn = mocker.patch.object(pexpect, "spawn")
    mock_spawn.return_value = mocker.Mock("spawn")

    for return_value in [3, 1, 0]:
        mock_spawn.return_value.expect = mocker.Mock(
            "expect", return_value=return_value
        )
        with pytest.raises(ConnectionError, match="Failed to establish ssh connection"):
            ssh_login_user(c, "user", "password")


def test_pxssh_login(c, mocker):
    mock_pxssh = mocker.patch.object(pxssh, "pxssh", return_value=mocker.Mock("pxssh"))
    mock_pxssh.return_value.login = mocker.Mock("login")
    pxssh_login(c, "user", "password")
    mock_pxssh.return_value.login.assert_called_with(
        socket.gethostname(), "user", "password"
    )


def test_pxssh_login_exception(c, mocker):
    mocker.patch("time.sleep")
    mock_pxssh = mocker.patch.object(
        pxssh, "pxssh", side_effect=pxssh.ExceptionPxssh("ERROR")
    )
    mock_error = mocker.patch("roast.ssh.log.error")
    with pytest.raises(ConnectionError, match="Failed to establish ssh connection"):
        pxssh_login(c, "user", "password")


def test_scp_file_transfer(c, mocker):
    c.sync = mocker.Mock("sync")
    c.sendline = mocker.Mock("sendline")
    c.prompt = mocker.Mock("prompt")
    c.expect = mocker.Mock("expect", return_value=0)
    c.config = {"images": "my_images", "target_path": "my_target_path"}
    call_password = mocker.call("root")
    call_scp = mocker.call(
        "scp -r -q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null my_images/* root@:my_target_path"
    )

    # proxy_server=None
    scp_file_transfer(c, timeout=10)
    c.sendline.assert_has_calls(
        [call_scp, call_password, call_password, call_password, call_password]
    )


def test_scp_file_transfer_proxy(c, mocker):
    c.sync = mocker.Mock("sync")
    c.sendline = mocker.Mock("sendline")
    c.prompt = mocker.Mock("prompt")
    c.expect = mocker.Mock("expect", return_value=0)
    c.config = {"images": "my_images", "target_path": "my_target_path"}
    call_password = mocker.call("root")
    call_scp = mocker.call(
        'scp -r -q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o "ProxyCommand ssh my_proxy -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -W %h:%p" my_images/* root@:my_target_path'
    )

    # proxy_server="my_proxy"
    scp_file_transfer(c, proxy_server="my_proxy", timeout=10)
    c.sendline.assert_has_calls(
        [call_scp, call_password, call_password, call_password, call_password]
    )


def test_scp_file_transfer_zero_return(c, mocker):
    c.sync = mocker.Mock("sync")
    c.sendline = mocker.Mock("sendline")
    c.prompt = mocker.Mock("prompt")
    c.config = {"images": "my_images", "target_path": "my_target_path"}
    call_scp = mocker.call(
        "scp -r -q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null my_images/* root@:my_target_path"
    )

    # index=1, exit_non_zero_return=0
    c.expect = mocker.Mock("expect", return_value=1)
    c._exit_non_zero_return = mocker.Mock("return_code", return_value=0)
    scp_file_transfer(c, timeout=10)
    c.sendline.assert_has_calls([call_scp])


def test_scp_file_transfer_from_target(c, mocker):
    c.sync = mocker.Mock("sync")
    c.sendline = mocker.Mock("sendline")
    c.prompt = mocker.Mock("prompt")
    c.expect = mocker.Mock("expect", return_value=0)
    c.config = {"images": "my_images", "host_path": "my_host_path"}
    call_password = mocker.call("root")
    call_scp = mocker.call(
        "scp -r -q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@:my_images/* my_host_path"
    )

    # transfer_to_target=False
    scp_file_transfer(c, transfer_to_target=False, timeout=10)
    c.sendline.assert_has_calls(
        [call_scp, call_password, call_password, call_password, call_password]
    )


def test_scp_file_transfer_exception(c, mocker):
    c.sync = mocker.Mock("sync")
    c.sendline = mocker.Mock("sendline")
    c.prompt = mocker.Mock("prompt")
    c.config = {"images": "my_images", "target_path": "my_target_path"}

    # index=2, exit_non_zero_return=1
    c.expect = mocker.Mock("expect", return_value=2)
    c._exit_non_zero_return = mocker.Mock("return_code", return_value=1)
    with pytest.raises(ConnectionError, match="Failed to scp"):
        scp_file_transfer(c, timeout=10)

    # index=3
    c.expect = mocker.Mock("expect", return_value=3)
    with pytest.raises(ConnectionError, match="Failed to scp"):
        scp_file_transfer(c, timeout=10)
