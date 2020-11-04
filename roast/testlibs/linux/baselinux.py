#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import logging

log = logging.getLogger(__name__)


class BaseLinux:
    def __init__(self, console, config):
        self.console = console
        self.config = config
        self.console._setup_init()
        self.console.exit_nzero_ret = True
        self.sys_dt_base = "/sys/firmware/devicetree/base"
        self.sys_amba = "/sys/devices/platform/amba"
        self.kconfig_path = "/proc/config.gz"
        self.sys_dmatest = "/sys/module/dmatest/parameters"
        self.bootargs = "/proc/cmdline"
        self.sys_devices = "/sys/devices"
        self.sys_class = "/sys/class"
        self.sys_class_dev = {
            "mmc": f"{self.sys_class}/mmc_host",
            "dma": f"{self.sys_class}/dma",
            "i2c": f"{self.sys_class}/i2c-adapter",
        }
        self.proc_kernel = "/proc/sys/kernel"

    def get_kernel_info(self):
        self.console.runcmd("uname -a", expected="\r\n")
        return self.console.output()

    def get_bootargs(self):
        self.console.runcmd(f"cat {self.bootargs}", expected="\r\n")
        return self.console.output()

    def capture_dmesg(self):
        self.console.runcmd("dmesg")
        with open(f"{self.config['ROOT']}/dmesg.txt", "w+") as f:
            f.write(str(self.console.output()))

    def set_console_loglevel(self, log_level="8"):
        self.console.runcmd(f"echo {log_level} > {self.proc_kernel}/printk")
        self.console.runcmd(f"cat {self.proc_kernel}/printk")
