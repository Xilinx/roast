#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import logging
import atexit
from roast.xexpect import Xexpect
from abc import ABCMeta, abstractmethod
from stevedore import driver

log = logging.getLogger(__name__)


class Serial:
    def __init__(self, serial_type: str, config, **kwargs) -> None:
        self._serial_mgr = driver.DriverManager(
            namespace="roast.serial",
            name=serial_type,
            invoke_on_load=True,
            invoke_args=(config,),
            invoke_kwds=kwargs,
        )

    @property
    def driver(self) -> driver:
        return self._serial_mgr.driver

    def exit(self) -> None:
        self.driver.exit()


class SerialBase(metaclass=ABCMeta):
    def __init__(self, config) -> None:
        self.config = config
        self.hostname = ""
        self.is_live = False
        self._configure()
        self.console = Xexpect(log, hostname=self.hostname, non_interactive=False)
        self.expect = self.console.expect
        self.sendline = self.console.sendline
        self.runcmd = self.console.runcmd
        self.runcmd_list = self.console.runcmd_list
        self.sendcontrol = self.console.sendcontrol
        self.send = self.console.send
        self.output = self.console.output
        self._setup_init = self.console._setup_init
        self.search = self.console.search
        self.sync = self.console.sync
        atexit.register(self.exit)
        self._connect()
        self.is_live = True

    def _configure(self) -> None:
        """Set hostname."""

    @abstractmethod
    def _connect(self) -> None:
        """Connect to host."""

    @abstractmethod
    def exit(self) -> None:
        """Release connection."""

    @property
    def prompt(self):
        return self.console.prompt

    @prompt.setter
    def prompt(self, value):
        self.console.prompt = value
