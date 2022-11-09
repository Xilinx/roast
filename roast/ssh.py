#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

"""
This lib was implemented with api calls to acquire host & target instances, scp file transffer.
"""

import os
import sys
import time
import pexpect
from pexpect import pxssh
import re
import socket
import logging
from typing import Optional
from roast.utils import convert_list, FileAdapter

log = logging.getLogger(__name__)


def scp_file_transfer(
    self,
    images: Optional[str] = None,
    target_path: Optional[str] = None,
    transfer_to_target: bool = True,
    host_path: Optional[str] = None,
    target_ip: str = "",
    proxy_server: Optional[str] = None,
    user: str = "root",
    password: str = "root",
    timeout: int = 3000,
) -> None:
    """Securely transfers file between host and target.

    Args:
        images: Image files to be transfered. Defaults to None.
        target_path: Path on target. Defaults to None.
        transfer_to_target: Transfer to target if True. Transfer from target if False. Defaults to True.
        host_path: Path on host. Defaults to None.
        target_ip: IP address of target. Defaults to "".
        proxy_server: Address of proxy server. Defaults to None.
        user: Username used for login. Defaults to "root".
        password: Password user for login. Defaults to "root".
        timeout: Time for expected output. Defaults to 3000.

    Raises:
        ConnectionError: When files fail to be transferred in within the timeout window.
    """
    if not images:
        images = f"{self.config['images']}/*"

    cmd = "scp -r -q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "
    if proxy_server:
        proxy_cmd = f'-o "ProxyCommand ssh {proxy_server} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -W %h:%p" '
        cmd += proxy_cmd

    # Send the file
    if transfer_to_target:
        if not target_path:
            target_path = f"{self.config['target_path']}"
        cmd += f"{images} {user}@{target_ip}:{target_path}"
    # Receive the file
    else:
        if not host_path:
            host_path = f"{self.config['host_path']}"
        cmd += f"{user}@{target_ip}:{images} {host_path}"

    err = f"Failed to scp {images} to {target_path}"
    expected_failures = [
        "lost connection",
        "Name or service not known",
        "Name or service not known",
        "Permission denied",
        "No such file or directory",
        "No route to host",
        "Network is unreachable",
        "No space left on device",
    ]
    expected = ["[Pp]assword", "Do you want to continue", self.hostname]

    if self.prompt:
        expected.append(self.prompt)

    self.sync()
    self.sendline(str(cmd))
    for n in range(5):
        index = self.expect(
            expected_failures,
            expected,
            wait_for_prompt=False,
            err_index=len(convert_list(expected_failures)),
            timeout=float(timeout),
        )
        if index == 0:
            self.sendline(password)
        elif index == 1:
            self.sendline("y")
        elif index in (2, 3):
            return_code = self._exit_non_zero_return(cmd, custom_err="Failed to scp")
            if return_code != 0:
                # Max re-tries exceeded
                if n >= 4:
                    raise ConnectionError(err)
            else:
                log.info(f"scp {images} to {target_path} successfully")
                break
        else:
            raise ConnectionError(err)


def pxssh_login(self, userid: str, password: str) -> None:
    for n in range(5):
        try:
            terminal = pxssh.pxssh()
            terminal.login(self.ip, userid, password)
            terminal.logfile = FileAdapter(log)
            log.info(f"Successfully established ssh connection with {self.ip}")
            self.terminal = terminal
            break
        except pxssh.ExceptionPxssh as e:
            log.info("ssh retry %s of %s \n %s" % (str(n), str(5), str(e)))
        time.sleep(1)
    if n >= 4:
        err = f"Failed to establish ssh connection with {self.ip}"
        log.error(err)
        raise ConnectionError(err)


def ssh_login_user(self, userid: str, password: str) -> None:
    sshcmd = f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {userid}@{self.ip} -y"
    terminal = pexpect.spawn(
        sshcmd, echo=self.echo, encoding="utf-8", codec_errors="replace"
    )
    terminal.logfile = FileAdapter(log)
    self.terminal = terminal
    for n in range(4):
        try:
            index = self.terminal.expect(
                [
                    pexpect.EOF,
                    pexpect.TIMEOUT,
                    "password:",
                    "Permission denied",
                    "(%|#|>|\\$|# )",
                ],
                timeout=60,
            )
            if index == 4:
                break
            elif index == 3:
                raise ConnectionError(f"{sshcmd} with incorrect password: {password}")
            elif index == 2:
                self.terminal.sendline(password)
            elif index == 1:
                raise ConnectionError(f"TIMEOUT wait for password while {sshcmd}")
            else:
                raise ConnectionError(
                    f"EOF while spawn {sshcmd} with password: {password}"
                )
        except ConnectionError as e:
            log.error(e)
        time.sleep(1)

    if n >= 3:
        err = f"Failed to establish ssh connection with {self.ip}, username:{userid} password:{password}"
        log.error(err)
        raise ConnectionError(err)
    self.terminal.sendline("/bin/bash --norc")
    self.terminal.expect("bash-", timeout=60)


def ssh_login(self) -> None:

    if self.hostname == socket.gethostname():
        sshcmd = "/bin/bash --norc"
    else:
        sshcmd = f"{self.cmd} {self.ip} '/bin/bash --norc'"

    terminal = pexpect.spawn(
        sshcmd, echo=self.echo, encoding="utf-8", codec_errors="replace"
    )
    terminal.logfile = FileAdapter(log)

    index = terminal.expect(
        [pexpect.EOF, pexpect.TIMEOUT, "bash-", "password:"], timeout=120
    )
    if index == 2:
        self.terminal = terminal
        if self.non_interactive:
            self.terminal.sendline("bash --norc | cat")
            self.terminal.expect("bash-", timeout=20)
        else:
            self.terminal.sendline("bash --norc")
            self.terminal.expect("bash-", timeout=20)

        self.runcmd(r"PS1='\u@\H:\t:\w\$ '", expected=self.hostname)
        log.info("New console on %s!" % self.ip)
    else:
        if index == 3:
            err = "Password less login not Enabled"
            log.error(err)
        raise ConnectionError(f"Failed to establish ssh connection with {self.ip}")
