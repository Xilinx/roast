#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from roast.machines.versal import *

uboot_devicetree = "versal-vmk180-revA-x-ebm-01-revA"
dtb_dtg = uboot_devicetree.lower()

PLNX_BSP = "xilinx-vmk180-v{version}-final.bsp"
plnx_proj = "xilinx-vmk180-{version}"
