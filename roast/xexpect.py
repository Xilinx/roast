#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import sys
import time
import re
import socket
import inspect
import asyncio
import logging
import atexit
import pexpect
from typing import Optional, Union, List
from roast.ssh import ssh_login_user, ssh_login
from roast.utils import convert_list, colorstr_to_plainstr


class Xexpect:
    """This Xexpect class is wrapper on pexpect"""

    sshcmd = "ssh -t -y -o StrictHostKeyChecking=no -X "

    def __init__(
        self,
        log: logging.Logger,
        hostname: str = socket.gethostname(),
        hostip: Optional[str] = None,
        userid: Optional[str] = None,
        password: Optional[str] = None,
        non_interactive: bool = True,
        exit_nzero_ret: bool = False,
        echo: bool = False,
    ):
        self.log = log
        self.hostname = hostname  # TODO Fix same host running
        self.cmd = self.sshcmd
        self.terminal = None
        self.non_interactive = non_interactive
        self.exit_nzero_ret = exit_nzero_ret  # if set, will assert on non zero returns
        self.echo = echo
        atexit.register(self.exit)
        self._setup_ip_prompt(hostip, hostname)
        self._setup_ssh(userid, password)
        self._setup_init()

    def _setup_ip_prompt(self, hostip, hostname):
        if hostip is None:
            self.ip = hostname
            self.prompt = hostname
        else:
            self.ip = hostip
            self.prompt = "(%|#|>|\\$|# )"

    def _setup_ssh(self, userid, password):
        if None not in (userid, password):
            ssh_login_user(self, userid, password)
        else:
            ssh_login(self)

    def _setup_init(self):
        # Disable History
        self.runcmd("set +o history", expected=self.prompt)

        # Source check_nzero_exit function
        # This function returns return code of a command
        cmd = "check_nzero_exit() { ret=$? ; if [ $ret -ne 0 ]; then echo returncode=$ret; fi ;}"
        self.runcmd(cmd, expected=self.prompt)

    def _exit_non_zero_return(self, cmd, custom_err=None):

        # Send exit status command.
        self.sendline("check_nzero_exit")
        # Expect for prompt
        self.terminal.expect(self.prompt)
        # Search fo return code
        matchObj = re.search(r"returncode=([\d+])", self.terminal.before)
        if matchObj is not None:
            returncode = matchObj.group(1)
            err_msg = f"{cmd} exited with returncode {returncode}"
            self.log.error(err_msg)
            if custom_err:
                self.log.error(err_msg)
            assert False, err_msg
        else:
            index = 0

        return index

    def runcmd(
        self,
        cmd: str,
        expected_failures: Union[None, List[str], str] = None,
        expected: Optional[List[str]] = None,
        wait_for_prompt: bool = True,
        timeout: int = 200,
        err_msg: Optional[str] = None,
        retries: int = 1,
    ) -> int:
        """Sends command on to the console with expected failures and expected output and returns the index of expected string.

        Args:
            cmd: Command to be executed on the console
            expected_failures: List of failure patterns or a single fail pattern string to be expected. Defaults to None.
            expected: List of strings or string. Defaults to None.
            wait_for_prompt: To specify if prompt has to be expected after expected pattern. Defaults to True.
            timeout: Waits for mentioned timeout for the expected string. Defaults to 200.
            err_msg: Error message. Defaults to None.
            retries: Number of retries. Defaults to 1.

        Returns:
            Index of the expected string.
        """

        def _runcmd():
            self.log.debug(f"cmd: {cmd}")
            self.sendline(cmd)
            index = self.expect(
                expected_failures,
                expected,
                wait_for_prompt=wait_for_prompt,
                timeout=timeout,
                err_index=len(convert_list(expected_failures)),
                err_msg=err_msg,
            )

            if self.exit_nzero_ret and not expected:
                index = self._exit_non_zero_return(cmd, custom_err=err_msg)
            return index

        for _ in range(retries - 1):
            try:
                ret = _runcmd()
                break  # break out of loop if success
            except Exception:
                self.log.info("Retrying...")
                time.sleep(10)
        else:
            ret = _runcmd()
        return ret

    def runcmd_list(
        self,
        cmd_list: List[str],
        expected: Optional[List[str]] = None,
        timeout: int = 200,
        err_msg: Optional[str] = None,
    ) -> None:
        """Sends list of commands to the console and expects the specified string.

        Args:
            cmd_list: List of commands to be run on console.
            expected: Expects for the same string for all the commands. If nothing is specified it expects for prompt. Defaults to None.
            timeout: Waits for mentioned timeout for the expected string. Defaults to 200.
            err_msg: Optional custom error message. Defaults to None.
        """

        for cmd in cmd_list:
            self.runcmd(cmd, expected=expected, timeout=timeout, err_msg=err_msg)

    def runcmd_async(self, cmd, expected=None, timeout=200):
        self.sendline(cmd)
        return self.expect_async(expected, timeout=timeout)

    def output(self):
        """Returns the output of the previous command executed"""
        return colorstr_to_plainstr(self.terminal.before.rstrip())

    def search(self, srch_str):
        """Takes a regular expression as input and outputs the string that matches the regular expression.

        Args:
            srch_str (str): Regular expression in braces

        Returns:
            str: Matched string.

        Example:
            search("([a-z][A-Z]+)")
        """
        match_obj = re.search(srch_str, self.output())

        if match_obj:
            return match_obj.group(1)
        else:
            return ""

    def send(self, cmd):
        """Sends the command on to the console

        Args:
            cmd (str): cmd to be sent on to the console.
        """
        self.terminal.sendline(cmd)

    def sendline(self, cmd):
        """Sends the command on to the console with linefeed.

        Args:
            cmd (str): cmd to be sent on to the console.
        """
        self.terminal.sendline(cmd)

    def sendcontrol(self, cmd):
        """Sends control characters on to the console.

        Args:
            cmd (str): Control characters to be sent on console.
        """
        self.terminal.sendcontrol(cmd)

    def interact(self):
        # Get Object instance
        """Gives control of the child process to the interactive user."""
        print("Interactive Console:", end="")
        self.terminal.interact()

    def expect(
        self,
        expected_failures: Union[None, List[str], str] = None,
        expected: Optional[List[str]] = None,
        wait_for_prompt: bool = True,
        err_index: int = 0,
        timeout: int = 200,
        err_msg: Optional[str] = None,
    ) -> int:
        """Seeks through the stream until a pattern is matched.

        Args:
            expected_failures: list of failure patterns or a single fail pattern string to be expected. Defaults to None.
            expected: List of patterns or a single pattern string to be expexted. Defaults to None.
            wait_for_prompt: Specify if prompt has to be expected. Defaults to True.
            err_index: Length of expected_failures list. Defaults to 0.
            timeout: Waits for mentioned timeout for the expected string. Defaults to 200.
            err_msg: Custom error message. Defaults to None.

        """

        def _expect(cons, expected, err_index, timeout):
            expected_list = convert_list(pexpect.EOF, pexpect.TIMEOUT, expected)

            err_index += 2
            index = self.terminal.expect(expected_list, timeout=timeout)
            msgs = convert_list(
                "ERROR: Expect returned EOF", "ERROR: Expect returned TIMEOUT", expected
            )
            if index < err_index:
                self.log.error(msgs[index])
                if err_msg:
                    self.log.error(err_msg)
                    raise Exception(err_msg)
                else:
                    raise Exception(msgs[index])
            return index - err_index

        # If expected is not the prompt, there is still info in buffer.
        # It is resulting in log interleaving, we have to expect console
        # to sync buffer
        cons = self
        if expected == None and self.prompt != None:
            expected = self.prompt

        expected_list = convert_list(expected_failures, expected)
        # raises exception when nothing is expected
        if len(expected_list) == 0:
            err_msg = "ERROR: Expected list is empty"
            self.log.error(err_msg)
            assert False, err_msg

        index = _expect(cons, expected_list, err_index, timeout)
        # Expect again if expected strings are not self.prompt
        if (
            cons.terminal.isalive()
            and wait_for_prompt
            and self.prompt != None
            and self.prompt != expected_list[index + err_index]
        ):
            # Making error index to 0, as prompt is expected
            _expect(cons, self.prompt, 0, timeout)
        return index

    def expect_async(self, expected=None, timeout=200):

        if expected is None:
            expected = self.prompt
        # TODO: mutex lock for coro
        self.coro = self.terminal.expect(
            [pexpect.EOF, pexpect.TIMEOUT, expected], async_=True, timeout=timeout
        )
        return

    def wait(self):
        return asyncio.get_event_loop().run_until_complete(self.coro)

    def sync(self):
        self.runcmd("echo 'sync' | tr '[a-z]' '[A-Z]'", expected=["SYNC"])

    def exit(self):
        if self.terminal:
            self.sendline("exit")
        time.sleep(3)
