#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from roast.machines.versal import *

PLNX_BSP = "xilinx-vck190-v{version}-final.bsp"
plnx_proj = "xilinx-vck190-{version}"
plnx_package_boot = True
uboot_devicetree = "versal-vck190-revA-x-ebm-01-revA"
dtb_dtg = uboot_devicetree.lower()
