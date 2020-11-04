#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#


class SysDevices:
    def get_channels(self, dts_list, peripheral):
        self.console.sync()
        self.channels = []
        for x in dts_list:
            self.console.runcmd(
                f"ls {self.sys_class_dev[peripheral]} -l | awk '{{print $NF}}'"
                f" | grep {x}",
                expected="\r\n",
            )
            self.channels.extend(self.console.output().split("\n"))
        self.channels = [s.split("/")[-1].rstrip() for s in self.channels]
        if not self.channels:
            assert False, f"No channels found for {peripheral} in sysfs"
        return self.channels
