#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import socket
import logging
from abc import ABCMeta, abstractmethod
from stevedore import driver
from roast.component.xsdb.xsdb import Xsdb
from roast.serial import Serial
from roast.xexpect import Xexpect
from roast.utils import has_key
from roast.component.board.relay import Relay
from roast.ssh import scp_file_transfer

log = logging.getLogger(__name__)
hlog = logging.getLogger(__name__ + ".host")
tlog = logging.getLogger(__name__ + ".target")


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


class TargetBoard(BoardBase):
    def __init__(self) -> None:
        super().__init__()

    def start(self) -> None:
        self.interface = self.config.get("board_interface")
        self.relay_type = self.config.get("relay_type")
        if self.interface == "host_target":
            self._setup_host_target()
            self.relay = Relay(self.relay_type, session=self.host_console).driver
            self._reboot()
            self.serial = Serial("host", self.config).driver

        elif self.interface == "network_target":
            self._set_nw_target()
            self.target_console = Xexpect(
                tlog,
                hostip=self.ip,
                userid=self.user,
                password=self.password,
                non_interactive=False,
            )
        elif self.interface == "qemu":
            log.info("Running Qemu Interface")
        else:
            raise Exception(f"ERROR: invalid board_interface {self.interface}")

    def _setup_host_target(self) -> None:
        self._set_host()
        if not self.isLive:
            self.host_console = Xexpect(
                hlog,
                hostname=self.host,
                non_interactive=False,
            )
            if self.invoke_hwserver:
                self.xsdb_hwserver = Xsdb(
                    self.config, hostname=self.host, setup_hwserver=True
                )
            if self.invoke_xsdb:
                self.xsdb = Xsdb(self.config, hwserver=self.host)
            self.isLive = True
        else:
            self.serial.exit()
            if self.invoke_xsdb:
                self.xsdb = Xsdb(self.config, hwserver=self.host)

    def _set_nw_target(self) -> None:
        self.ip = self.config["target_ip"]
        self.user = self.config["user"]
        self.password = self.config["password"]

    def _reboot(self) -> None:
        if self.isLive and self.reboot:
            if self.interface == "host_target":
                self.relay.reconnect()

    def put(self, src_file: str, dest_path: str) -> None:
        self._get_target_ip()
        if not self.target_ip:
            assert False, "ERROR: Not a valid target ip"
        if self.interface == "host_target":
            scp_file_transfer(
                self.host_console,
                src_file,
                dest_path,
                target_ip=self.target_ip,
                proxy_server=self.host,
            )

    def get(self, src_file: str, dest_path: str) -> None:
        self._get_target_ip()
        if self.interface == "host_target":
            scp_file_transfer(
                self.host_console,
                src_file,
                host_path=dest_path,
                transfer_to_target=False,
                target_ip=self.target_ip,
                proxy_server=self.host,
            )

    def reset(self) -> None:
        if self.isLive:
            if self.interface == "host_target":
                self.relay.reconnect()
