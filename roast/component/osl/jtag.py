#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

"""
This Module holds methods that performs Linux Boot on target in Osl flow.

"""

import pytest
import os
from time import sleep
from roast.utils import has_key
from roast.component.board.boot import linux_login_cons
from roast.component.board.board import Board


class BaseBoot:
    def __init__(self, xsdbcon):
        self.xsdbcon = xsdbcon

    def load_pmufw(self, elf_path):
        self.xsdbcon.load_elf(elf_path)
        sleep(5)

    def load_fsbl(self, fsbl_path):
        self.xsdbcon.load_elf(fsbl_path)
        sleep(5)

    def load_devicetree(self, dtb_path, dtb_loadaddr=0x100000):
        self.xsdbcon.load_data(dtb_path, dtb_loadaddr, timeout=400)
        sleep(5)

    def load_kernel(self, kernel_path, kernel_loadaddr=0x200000):
        self.xsdbcon.load_data(kernel_path, kernel_loadaddr, timeout=400)
        sleep(2)

    def load_rootfs(self, rootfs_path, rootfs_loadaddr=0x04000000):
        self.xsdbcon.load_data(rootfs_path, rootfs_loadaddr, timeout=800)
        sleep(5)

    def load_boot_scr(self, boot_scr_path, boot_scr_loadaddr=0x20000000):
        self.xsdbcon.load_data(boot_scr_path, boot_scr_loadaddr, timeout=400)
        sleep(5)

    def load_uboot(self, uboot_path):
        self.xsdbcon.load_elf(uboot_path)
        sleep(5)

    def load_atf(self, atf_path):
        self.xsdbcon.load_elf(atf_path)
        sleep(5)

    def load_bitstream(self, bitfile_path):
        self.xsdbcon.fpga(bitfile_path)
        sleep(5)

    def set_proc(self, proc):
        self.xsdbcon.set_proc(proc)


class BootZynqmp(BaseBoot):
    def __init__(self, xsdbcon, ImagesDir, config):
        self.xsdbcon = xsdbcon
        self.images_dir = ImagesDir
        self.config = config
        self.proc = self.config["processor"]
        super().__init__(self.xsdbcon)

    def _linux_boot(self):
        self._load_pmufw()
        self._load_fsbl()
        self._load_bitstream()
        self._load_devicetree()
        self._load_kernel()
        self._load_rootfs()
        self._load_boot_scr()
        self._load_uboot()
        self._load_atf()
        self.xsdbcon.runcmd("con")
        sleep(1)
        self.xsdbcon.disconnect()

    def _uboot_boot(self):
        self._load_pmufw()
        self._load_fsbl()
        self._load_bitstream()
        self._load_devicetree()
        self._load_uboot()
        self._load_atf()
        self.xsdbcon.runcmd("con")
        sleep(1)
        self.xsdbcon.disconnect()

    def _load_pmufw(self):
        macros = {"0xffca0038": "0x1ff"}
        self.xsdbcon.set_proc(self.proc["PSU"])
        self.xsdbcon.write(macros)
        self.set_proc(self.proc["MB_PMU"])
        self.load_pmufw(f"{self.images_dir}/pmufw.elf")
        self.xsdbcon.runcmd("con")

    def _load_fsbl(self):
        self.set_proc(self.proc["a53_0"])
        self.xsdbcon.rst_proc()
        self.load_fsbl(f"{self.images_dir}/zynqmp_fsbl.elf")
        self.xsdbcon.runcmd("con")
        sleep(2)
        self.xsdbcon.runcmd("stop")

    def _load_bitstream(self):
        if has_key(self.config, "is_rfdc_board") and self.config["is_rfdc_board"]:
            Isolation_Data = {"0xFFD80118": "0x00800000", "0xFFD80120": "0x00800000"}
            Pl_logic_reset = {
                "0xFF0a002C": "0x80000000",
                "0xFF0A0344": "0x80000000",
                "0xFF0A0348": "0x80000000",
                "0xFF0A0054": "0x0",
            }
            macros = {"0xFF0A0054": "0x80000000"}
            validate_macros = {"0xFF0A0344": "0x80000000", "0xFF0A0348": "0x80000000"}
            self.load_bitstream(f"{self.images_dir}/system.bit")
            self.xsdbcon.write(Isolation_Data)
            self.xsdbcon.write(Pl_logic_reset)
            self._validate_address(validate_macros)
            sleep(5)
            self.xsdbcon.write(macros)
            sleep(5)

    def _validate_address(self, addr_value):
        for addr, value in addr_value.items():
            reg_value = self.xsdbcon.read(addr)
            assert hex(int(reg_value[0])) == value, "ERROR: Register value mismatch"

    def _load_kernel(self):
        self.load_kernel(f"{self.images_dir}/Image", self.config["kernel_loadaddr"])

    def _load_rootfs(self):
        self.load_rootfs(
            self.config["rootfs_path_full"], self.config["rootfs_loadaddr"]
        )

    def _load_devicetree(self):
        self.load_devicetree(
            f"{self.images_dir}/{self.config['system_dtb']}",
            self.config["dtb_loadaddr"],
        )

    def _load_boot_scr(self):
        self.load_boot_scr(
            self.config["boot_scr_path_full"], self.config["boot_scr_loadaddr"]
        )

    def _load_atf(self):
        self.load_atf(f"{self.images_dir}/bl31.elf")

    def _load_uboot(self):
        self.load_uboot(f"{self.images_dir}/u-boot.elf")


class BootZynq(BootZynqmp):
    def __init__(self, xsdbcon, ImagesDir, config):
        super().__init__(xsdbcon, ImagesDir, config)

    def _linux_boot(self):
        self.set_proc(self.proc["ARM"])
        self._load_fsbl()
        self.xsdbcon.runcmd("con")
        sleep(2)
        self.xsdbcon.runcmd("stop")
        sleep(3)
        self.set_proc(self.proc["ARM"])
        self._load_uboot()
        sleep(2)
        self.xsdbcon.runcmd("con")
        sleep(1)
        self.xsdbcon.runcmd("stop")
        self.set_proc(self.proc["ARM"])
        sleep(2)
        self._load_kernel()
        self._load_rootfs()
        self._load_devicetree()
        self._load_boot_scr()
        self.xsdbcon.runcmd("con")
        sleep(5)
        self.xsdbcon.disconnect()

    def _uboot_boot(self):
        self.set_proc(self.proc["ARM"])
        self._load_fsbl()
        self.xsdbcon.runcmd("con")
        sleep(5)
        self.xsdbcon.runcmd("stop")
        self.set_proc(self.proc["ARM"])
        self._load_uboot()
        sleep(5)
        self.xsdbcon.runcmd("con")
        sleep(5)
        self.xsdbcon.runcmd("stop")
        self.set_proc(self.proc["ARM"])
        sleep(5)
        self._load_devicetree()
        self.xsdbcon.runcmd("con")
        sleep(5)
        self.xsdbcon.disconnect()

    def _load_fsbl(self):
        self.load_fsbl(f"{self.images_dir}/zynq_fsbl.elf")

    def _load_kernel(self):
        self.load_kernel(f"{self.images_dir}/uImage")


class BootMicroblaze(BootZynqmp):
    def __init__(self, xsdbcon, ImagesDir, config):
        super().__init__(xsdbcon, ImagesDir, config)

    def _load_fsbl(self):
        self.load_fsbl(f"{self.images_dir}/simpleImage.system")

    def _load_bitstream(self):
        self.load_bitstream(f"{self.images_dir}/system.bit")

    def _linux_boot(self):
        self._load_bitstream()
        sleep(2)
        self.set_proc(self.proc["MB"])
        self.xsdbcon.runcmd("catch {stop}")
        self._load_fsbl()
        self.xsdbcon.runcmd("con")
        sleep(5)
        self.xsdbcon.disconnect()


class BootVersal(BootZynqmp):
    def __init__(self, xsdbcon, ImagesDir, config):
        super().__init__(xsdbcon, ImagesDir, config)

    def _linux_boot(self):
        self.xsdbcon.device_program(self.config["pdi_file"])
        self.set_proc(self.proc["a72_0"])
        self.xsdbcon.rst_proc()
        self._load_devicetree()
        self._load_kernel()
        self._load_rootfs()
        self._load_boot_scr()
        self._load_uboot()
        self._load_atf()
        self.xsdbcon.runcmd("con")

    def _uboot_boot(self):
        self.xsdbcon.device_program(self.config["pdi_file"])
        self.set_proc(self.proc["a72_0"])
        self.xsdbcon.rst_proc()
        self._load_devicetree()
        self._load_uboot()
        self._load_atf()
        self.xsdbcon.runcmd("con")


class JtagBoot:
    def __init__(self, Xsdbcon, config, ImagesDir, variant, boot="linux"):
        self.config = config
        self.xsdbcon = Xsdbcon
        self.config = config
        self.images_dir = ImagesDir
        self.variant = variant
        self.boot = boot
        self.set_rootfs()
        self.config["boot_scr_path_full"] = os.path.join(
            self.config["boot_scr_path"], f"{self.variant}.scr"
        )

        class_dict = {
            "zynqmp": BootZynqmp,
            "zynq": BootZynq,
            "microblaze": BootMicroblaze,
            "versal": BootVersal,
        }
        # Instatiating Boot class based on variant passed
        BootLinux = class_dict[self.variant](self.xsdbcon, self.images_dir, self.config)
        getattr(BootLinux, f"_{self.boot}_boot")()

    def set_rootfs(self):
        self.rootfs_full_path = ""
        self.rootfs_path = os.path.join(self.config["rootfs_path"], self.variant)
        for file in os.listdir(self.rootfs_path):
            if file.endswith("rootfs.cpio.gz.u-boot"):
                self.rootfs_full_path = os.path.join(self.rootfs_path, file)
        if not self.rootfs_full_path:
            assert "Rootfs is Not found in path"
        else:
            self.config["rootfs_path_full"] = self.rootfs_full_path


if __name__ == "__main__":
    # Instantiate JtagBoot with xsdbcon, config, ImagesDir and Platform
    linux_osl = JtagBoot(board.xsdb, config, images_dir, variant)
    # Validate for Linux console
    linux_login_cons(
        board.serial, user="root", password="root", login=True, timeout=300
    )
