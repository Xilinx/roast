#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

ROOT = ""
buildDir = "{ROOT}/build"

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

mylist = ["a", "b"]
