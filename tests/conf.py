#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from box import Box

a = Box(default_box=True)
a.b = "2020.1"

# This should not take effect as base parameters cannot be overriden in standard configuration.
# If required, must use override mechanism.
ROOT = ""

# hwflow
version = "2020.2"
build = "{version}_daily_latest"
VIVADO = "/proj/xbuilds/{build}/installs/lin64/Vivado/{version}/bin/vivado"
hwflow_ver = "1.0"
lsf_mode = False
lsf_options = "-Is"
lsf_queue = "long"
lsf_osver = "ws7"
lsf_mem = "65536"

# dtg
dtb_arch = "aarch64"

# override tests
mylist = ["a", "b"]
b = Box(default_box=True)
b.a = "hello"
b.b = "hello again"

# missing variable
missingvar = "{novar} test"

del Box
