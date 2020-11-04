#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#


class Kconfig:
    def check_kernel_config(self, kernel_configs=None):
        status_list = []
        status = [True, False, True]
        for config in kernel_configs:
            search_list = [f"{config}=y", f"# {config} is not set", f"{config}=m"]
            self.console.runcmd(
                f"zcat {self.kconfig_path} | grep {config}", expected="\r\n"
            )
            for idx, item in enumerate(search_list):
                if item in self.console.output():
                    status_list.append(status[idx])
        return status_list
