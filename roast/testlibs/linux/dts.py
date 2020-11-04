#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import logging

log = logging.getLogger(__name__)


class DtsLinux:
    def check_dt_node_status(self, dts_base=None, dt_nodes=None):
        if not dts_base:
            dts_base = self.sys_dt_base
        node_status = []
        for dt_node in dt_nodes:
            self.dts_path = f"{dts_base}/{dt_node}/status"
            self.console.runcmd(f"cat {self.dts_path}", expected="\r\n")
            if (
                "ok" in self.console.output()
                and "disabled" not in self.console.output()
            ):
                node_status.append(True)
            else:
                node_status.append(False)
        return node_status

    def list_dts_parameters(self, node_path, parameter=None):
        self.console.sync()
        self.console.runcmd(
            f"ls {self.sys_dt_base}/{node_path}/{parameter}", expected="\r\n"
        )
        if not self.console.output():
            log.info(f"No dts entries found for {node_path}")
            return False
        return self.console.output().split()

    def get_dts_nodes(self, dts_list, Ip):
        self.dts_nodes = []
        for node in dts_list:
            self.console.sync()
            self.console.runcmd(f"cat {node}", expected="\r\n")
            if Ip in self.console.output():
                self.dts_nodes.append(node.split("/")[-2][4:])
        if not self.dts_nodes:
            assert False, f"dts nodes not found for {Ip} IP"
        return self.dts_nodes
