#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

ROOT = ""
buildDir = "{ROOT}/tests/test_hwflow/_tmp"

# Settings to test hwflow package version 4.1
hwflow_ver = "2.0"
version = "2020.2"
build = "2020.2_INT_0810_1"
VIVADO = "/proj/xbuilds/{build}/installs/lin64/Vivado/{version}/bin/vivado"

# Design script and outputs
design_name = "versal_3bram"
design_script = "{ROOT}/tests/test_hwflow/{design_name}.py"
artifacts = [
    "outputs",
    "@design.runs/impl_1/gen_files",
    "@design.runs/impl_1/static_files",
    "@design.runs/impl_1/@design_wrapper.pdi.bif",
    "main.tcl",
    "config_bd.tcl",
    "vivado.log",
]
deploy_dir = "{buildDir}/hwflow_images/{version}/{build}/{design_name}"

# LSF settings
lsf_mode = False
lsf_options = "-Is"
lsf_queue = "long"
lsf_osver = "ws7"
lsf_mem = "65536"
lsf_xsjbsub = ""

# Hardware flow repo settings
hwflow_url = "git@gitenterprise.xilinx.com:SET-HW/hwflow2_0.git"
hwflow_branch = "master"
