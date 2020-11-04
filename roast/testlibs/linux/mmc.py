#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from roast.testlibs.linux.fileops import FileOps
from roast.testlibs.linux.baselinux import BaseLinux
from roast.testlibs.linux.kconfig import Kconfig
from roast.testlibs.linux.dts import DtsLinux


class MmcLinux(FileOps, Kconfig, DtsLinux, BaseLinux):
    def __init__(self, console, config):
        super().__init__(console, config)

    def get_mmc_list(self, device):
        self.mmc = {
            "sd": "SD",
            "emmc": "MMC",
        }
        self.mmc_type = self.mmc[device]
        self.mmc_list = []
        self.console.sync()
        self.console.runcmd(f"ls {self.sys_class_dev['mmc']}", expected="\r\n")
        if not self.console.output():
            assert False, f"{device} not found"
        else:
            mmc_nodes = self.console.output().split()
            for node in mmc_nodes:
                self.console.runcmd(
                    f"cat {self.sys_class_dev['mmc']}/{node}/*/uevent", expected="\r\n"
                )
                if f"MMC_TYPE={self.mmc_type}" in self.console.output():
                    mmc_device = "/dev/mmcblk" + node[-1]
                    self.mmc_list.append(mmc_device)
        if not self.mmc_list:
            assert False, f"{device} not found"
        return self.mmc_list

    def isUp(self, device):
        self.capture_dmesg()
        self.mmc_device_list = self.get_mmc_list(device)
        return self.mmc_device_list
