#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

platform = "zynq"
procs = ["A9"]
serial_port = "serial"

arch = "arm"
linux_compiler = "arm-linux-gnueabihf-"

kernel_loadaddr = 0x200000
kernel_defconfig = "xilinx_zynq_defconfig"
kernel_artifacts = ["arch/arm/boot/uImage"]

dtb_arch = "arm"
dtb_loadaddr = 0x100000

uboot_defconfig = "xilinx_zynq_virt_defconfig"
uboot_artifacts = ["u-boot.elf"]

boot_scr_path = "{dataDir}/scr"
boot_scr_loadaddr = 0x3000000

rootfs_loadaddr = 0x4000000
overrides = ["zynq"]

system_dtb = "{uboot_devicetree}.dtb"
