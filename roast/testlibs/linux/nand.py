#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#


class NandLinux:
    def isUP(self):
        self.capture_dmesg()
        return self.is_mtd_exist("nand")
