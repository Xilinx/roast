#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import logging

log = logging.getLogger(__name__)


class SysDevices:
    def get_channels(self, dts_list, peripheral):
        self.console.sync()
        self.channels = []
        for dt_node in dts_list:
            self.console.runcmd(
                f"ls {self.sys_class_dev[peripheral]} -l | awk '{{print $NF}}'"
                f" | grep {dt_node}",
                expected="\r\n",
            )
            if not self.console.output():
                log.info(f"No channels found for {dt_node}")
            else:
                self.channels.extend(self.console.output().split("\n"))
        self.channels = [s.split("/")[-1].rstrip() for s in self.channels]
        return self.channels
