#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from roast.testlibs.linux.baselinux import BaseLinux
from roast.testlibs.linux.dts import DtsLinux
from roast.testlibs.linux.sysdevices import SysDevices


class DmaLinux(DtsLinux, SysDevices, BaseLinux):
    def __init__(self, console, config):
        super().__init__(console, config)

    def isUp(self, dmaIp, dma_nodes_path="amba/dma*"):
        self.capture_dmesg()
        self.dma_dts_list = self.list_dts_parameters(
            dma_nodes_path, parameter="compatible"
        )
        self.dma_dts_nodes = self.get_dts_nodes(self.dma_dts_list, dmaIp)
        return self.get_channels(self.dma_dts_nodes, "dma")

    def dma_run(self):
        self.console.runcmd(
            f"echo 1 > {self.sys_dmatest}/run",
            expected="KB",
            timeout=1000,
            wait_for_prompt=False,
        )

    def dmatest_cfg_iterations(self, iterations):
        self.console.runcmd(f"echo {iterations} > {self.sys_dmatest}/iterations")

    def dmatest_cfg_threads(self, threads):
        self.console.runcmd(f"echo {threads} > {self.sys_dmatest}/threads_per_chan")

    def dmatest_cfg_mode(self, mode):
        self.console.runcmd(f"echo {mode} > {self.sys_dmatest}/dmatest")

    def dmatest_cfg_noverify(self, noverify):
        self.console.runcmd(f"echo {noverify} > {self.sys_dmatest}/noverify")

    def dmatest_cfg_bufsize(self, bufsize):
        self.console.runcmd(f"echo {bufsize} > {self.sys_dmatest}/test_buf_size")

    def dmatest_cfg_channel(self, channels_list=None):
        if channels_list is None:
            self.console.runcmd(f"echo ' ' > {self.sys_dmatest}/channel")
        else:
            for channel in channels_list:
                self.console.runcmd(f"echo {channel} > " f"{self.sys_dmatest}/channel")

    def dmatest_cfg_timeout(self, timeout):
        self.console.runcmd(f"echo {timeout} > {self.sys_dmatest}/timeout")

    def dma_print_result(self):
        val1 = self.console.output().count(": summary ")
        val2 = self.console.output().count(", 0 failures")
        if val1 == 0 or val1 != val2:
            assert False, "dma test failed"
