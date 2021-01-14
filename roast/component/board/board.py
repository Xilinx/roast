#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import socket
from abc import ABCMeta, abstractmethod
from stevedore import driver


class BoardBase(metaclass=ABCMeta):
    def __init__(self) -> None:
        self.config = {}
        self.isLive = False
        self.reboot = False
        self.serial = None
        self.xsdb = None
        self.invoke_hwserver = True
        self.invoke_xsdb = True
        self.host_console = None
        self.target_console = None
        self.target_ip = None
        self.host = None
        self.first_boot = True

    @abstractmethod
    def start(self) -> None:
        """Initiate connection."""

    @abstractmethod
    def put(self, src_file: str, dest_path: str) -> None:
        """Transfer file to target.

        Args:
            src_file (str): Path to file.
            dest_path (str): Target file path.
        """

    @abstractmethod
    def get(self, src_file: str, dest_path: str) -> None:
        """Tranfer file from target.

        Args:
            src_file (str): Target file path.
            dest_path (str): Path to file.
        """

    @abstractmethod
    def reset(self) -> None:
        """Reset or reconnect."""

    def _set_host(self) -> None:
        self.host = self.config.get("remote_host", socket.gethostname())

    def _get_target_ip(self) -> None:
        if not self.target_ip:
            self.serial.sendline("ifconfig eth0")
            self.serial.expect("# ")
            self.target_ip = self.serial.search(
                "inet addr:([0-9]+.[0-9]+.[0-9]+.[0-9]+)"
            )


class Board:
    def __init__(self, board_type: str) -> None:
        self._board_mgr = driver.DriverManager(
            namespace="roast.board",
            name=board_type,
            invoke_on_load=True,
        )

    @property
    def driver(self):
        return self._board_mgr.driver

    def start(self) -> None:
        self.driver.start()

    def put(self, src_file, dest_path) -> None:
        self.driver.put(src_file, dest_path)

    def get(self, src_file, dest_path) -> None:
        self.driver.get(src_file, dest_path)

    def reset(self) -> None:
        self.driver.reset()
