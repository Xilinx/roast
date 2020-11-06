#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import re
import logging

log = logging.getLogger(__name__)


class FileOps:
    def get_disk_nodes(self, device, extra_ops=""):
        nodes = []
        self.console.sync()
        cmd = f"find /dev/disk/by-id/ -type l \( -name '*{device}*' {extra_ops} \) -a ! -iname '*part*'"
        self.console.runcmd(cmd, expected="\r\n")
        if not self.console.output():
            assert False, f"{device} not found"
        else:
            found_nodes = self.console.output().split("\n")
        for node in found_nodes:
            self.console.sync()
            self.console.runcmd(f"readlink -f {node}", expected="\r\n")
            nodes.append(self.console.output())
        nodes = list(dict.fromkeys(nodes))
        return nodes

    def is_mount(self, device):
        self.console.sync()
        self.console.runcmd(f"mount | grep -w {device}", expected="\r\n")
        if device in self.console.output():
            return True
        else:
            return False

    def unmount(self, device):
        self.device_list = []
        if isinstance(device, dict):
            for dev, partitions in device.items():
                self.device_list.append(dev)
                for part in partitions:
                    self.device_list.append(part)
        elif isinstance(device, list):
            self.device_list = device
        else:
            self.device_list = [device]

        for device in self.device_list:
            if self.is_mount(device):
                self.console.runcmd(f"umount {device}")

    def mount(self, device, mnt_path, filesystem=None):
        self.unmount([device, mnt_path])
        extra_opts = ""
        if filesystem:
            extra_opts = f"-t {filesystem}"
        cmd = f"mount {extra_opts} {device} {mnt_path}"
        self.console.runcmd(cmd)

    def device_erase(self, device, bs="1024", count="1"):
        partitions = self.get_partition_list([device])
        self.unmount(partitions)
        cmd = f"dd if=/dev/zero of={device} bs={bs} count={count}"
        self.console.runcmd(cmd)

    def create_partition(self, device):
        cmd = "echo -e 'p\nn\np\n1\n\n+800M\nw\n' | " f"fdisk '{device}'"
        self.console.runcmd(cmd)
        self.unmount(f"{device}1")

    def createfile(self, file_name, size, count):
        cmd = f"dd if=/dev/urandom of={file_name} bs={size} count={count}"
        self.console.runcmd(cmd, expected="\r\n")

    def createdir(self, dir_name):
        cmd = f"mkdir -p {dir_name}"
        self.console.runcmd(cmd, expected="\r\n")

    def removefile(self, filename):
        cmd = f"rm -rf {filename}.*"
        self.console.runcmd(cmd, expected="\r\n")

    def copyfile(self, src, dest):
        self.console.runcmd(f"cp {src} {dest}")

    def clear_cache(self, clear_option):
        self.console.sync()
        self.console.runcmd(f"echo {clear_option} > /proc/sys/vm/drop_caches")

    def compfile(self, src, dest):
        self.console.runcmd(f"md5sum {src} | cut -d ' ' -f1", expected="\r\n")
        file1 = re.findall(r"([a-fA-F\d]{32})", self.console.output())
        self.console.runcmd(f"md5sum {dest} | cut -d ' ' -f1", expected="\r\n")
        file2 = re.findall(r"([a-fA-F\d]{32})", self.console.output())
        return file1 == file2

    def file_system_format(self, device, file_system, fat_size="32"):
        self.unmount(device)
        if file_system == "vfat":
            extra_opts = f"-F {fat_size}"
        else:
            extra_opts = "-F"
        self.console.runcmd(f"mkfs.{file_system} {device} {extra_opts}")

    def is_file_exist(self, file_path, silent_discard=True):
        try:
            self.console.runcmd(f"ls {file_path}")
            return True
        except:
            if not silent_discard:
                log.info(f"'{file_path}': No such file or directory")
            return False

    def get_file_size(self, file_path):
        self.console.runcmd(f"ls -l {file_path} | awk '{{print $5}}'", expected="\r\n")
        return self.console.output()

    def get_partition_list(self, device_list):
        device_partitions_dict = {}
        for device in device_list:
            partitions_list = []
            output_list = []
            self.console.runcmd(f"ls {device}* | awk '{{print $NF}}'", expected="\r\n")
            output_list = self.console.output().split("\r\n")
            for element in output_list:
                partitions_list.append(element.strip())
            partitions_list.remove(device)
            device_partitions_dict.update({device: partitions_list})
        if not device_partitions_dict:
            assert False, f"{device_partitions_dict} not found"
        return device_partitions_dict

    def get_device_size(self, device_list):
        self.device_sizes_list = []
        for device in device_list:
            self.console.runcmd(f"fdisk -l {device}")
            self.device_size = self.console.output()[f"{device}: ":", "]
            self.device_sizes_list.append(self.device_size)
        return self.device_sizes_list
