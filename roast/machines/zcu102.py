#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from roast.machines.zynqmp import *

uboot_devicetree = "zynqmp-zcu102-rev1.0"
dtb_dtg = "zcu102-rev1.0"
silicon = "da7"

PLNX_BSP = "xilinx-zcu102-v{version}-final.bsp"
plnx_proj = "xilinx-zcu102-{version}"
