#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

platform = "versal"
procs = ["a72", "R5", "PLM"]
serial_port = "com0"


arch = "arm64"
linux_compiler = "aarch64-linux-gnu-"
kernel_loadaddr = 0x80000

kernel_defconfig = "xilinx_defconfig"
kernel_artifacts = ["arch/arm64/boot/Image"]
uboot_defconfig = "xilinx_versal_virt_defconfig"

dtb_arch = "aarch64"
dtb_loadaddr = 0x1000
# FIXME: make it variable specific
uboot_artifacts = ["u-boot.elf", "arch/arm/dts/{system_dtb}"]

atf_artifacts = ["versal/release/bl31/bl31.elf"]
atf_compile_flags = "RESET_TO_BL31=1 PLAT=versal bl31 VERSAL_PLATFORM=silicon \
BUILD_BASE=../atf-build"

# Boot scr
boot_scr_path = "{dataDir}/scr"
boot_scr_loadaddr = 0x20000000

rootfs_loadaddr = 0x30000000
overrides = ["versal"]

system_dtb = "{uboot_devicetree}.dtb"
