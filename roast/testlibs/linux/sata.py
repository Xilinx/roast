#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import logging
from roast.testlibs.linux.baselinux import BaseLinux
from roast.testlibs.linux.fileops import FileOps

log = logging.getLogger(__name__)


class SataLinux(FileOps, BaseLinux):
    def __init__(self, console, config):
        super().__init__(console, config)

    def isUP(self):
        self.capture_dmesg()
        return self.get_disk_nodes("ata")

    def sata_dd_rw_vfat(self, sata_device, bs="1024", count="1", type_mode="vfat"):
        self.sata_dd_rw_common(sata_device, bs, count, type_mode)

    def sata_dd_rw_ext4(self, sata_device, bs="1024", count="1", type_mode="ext4"):
        self.sata_dd_rw_common(sata_device, bs, count, type_mode)

    def sata_dd_rw_common(self, sata_device, bs="1024", count="1", type_mode="vfat"):
        self.unmount(sata_device)
        self.console.runcmd(
            f"dd if=/dev/zero of='{sata_device}' bs=1024 count=1", expected="\r\n"
        )
        self.console.runcmd(
            f"echo -e 'p\nn\np\n1\n\n+800M\nw\n' | fdisk '{sata_device}'",
            expected="\r\n",
        )
        if type_mode == "vfat":
            self.console.runcmd(
                f"mkdir -p /mnt_sata;mkfs.vfat -F 32 '{sata_device}1'", expected="\r\n"
            )
        if type_mode == "ext4":
            self.console.runcmd(
                f"mkdir -p /mnt_sata;echo y | mkfs.ext4 -L root '{sata_device}1'",
                expected="\r\n",
            )
        self.console.runcmd(f"mount '{sata_device}1' /mnt_sata", expected="\r\n")
        self.console.runcmd(
            f"dd if=/dev/urandom of=/tmp/test.bin bs='{bs}' count='{count}'",
            expected="\r\n",
        )
        self.console.runcmd(f"cp /tmp/test.bin /mnt_sata/", expected="\r\n")
        self.console.sync()
        self.console.runcmd(f"echo 3 > /proc/sys/vm/drop_caches", expected="\r\n")

        diff = self.compfile("/tmp/test.bin", "/mnt_sata/test.bin")
        if diff:
            log.info(f">>> TEST PASS: SATA_dd_rw_{type_mode}")
        else:
            assert False, f">>> TEST FAIL: SATA_dd_rw_{type_mode}"

        self.unmount(f"{sata_device}1")
