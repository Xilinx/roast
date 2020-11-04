#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

platform = "zynqmp"
procs = ["A53", "R5"]
serial_port = "serial"

arch = "arm64"
linux_compiler = "aarch64-linux-gnu-"

kernel_loadaddr = 0x200000
kernel_defconfig = "xilinx_defconfig"
kernel_artifacts = ["arch/arm64/boot/Image"]

dtb_arch = "aarch64"
dtb_loadaddr = 0x100000

uboot_defconfig = "xilinx_zynqmp_virt_defconfig"
uboot_artifacts = ["u-boot.elf"]

atf_artifacts = ["zynqmp/release/bl31/bl31.elf"]
atf_compile_flags = "RESET_TO_BL31=1 PLAT=zynqmp bl31 ZYNQMP_PLATFORM=silicon \
BUILD_BASE=../atf-build"

boot_scr_path = "{dataDir}/scr"
boot_scr_loadaddr = 0x20000000

rootfs_loadaddr = 0x4000000
overrides = ["zynqmp"]

system_dtb = "{uboot_devicetree}.dtb"
