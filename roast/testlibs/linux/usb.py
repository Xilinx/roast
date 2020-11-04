#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import re
import logging
from roast.testlibs.linux.baselinux import BaseLinux
from roast.testlibs.linux.fileops import FileOps

log = logging.getLogger(__name__)


class UsbLinux(FileOps, BaseLinux):
    def __init__(self, console, config):
        super().__init__(console, config)

    def isUP(self, extra_ops=""):
        self.capture_dmesg()
        return self.get_disk_nodes("usb", extra_ops)

    def usb_peripheral_gadget(
        self,
        test,
        usb_node,
        manufacture="xilinx",
        vendor_id="0x0781",
        product_id="0x0104",
    ):
        if "mass_storage" in test:
            self.gadget = "mass_storage.ms0"
            cmd = "dd if=/dev/zero of=/tmp/mydev bs=1M count=256"
        elif "ethernet" in test:
            self.gadget = "ecm.usb0"
            cmd = "ifconfig -a"
        elif "serial" in test:
            self.gadget = "acm.usb0"
            cmd = "ls /dev/tty*"
        self.console.runcmd(cmd)

        self.platform = self.config.platform
        self.sys_kernel = "/sys/kernel/config/"
        self.strings_path = "strings/0x409/"
        self.gadget_configs = "configs/c1.1/"

        if self.platform == "zynq":
            self.console.runcmd("modprobe libcomposite")

        cmdlist = [
            "sync",
            f"mount -t configfs none {self.sys_kernel}",
            f"cd {self.sys_kernel}",
            "mkdir g1",
            "cd g1",
            "echo '64' > bMaxPacketSize0",
            "echo '0x200' > bcdUSB",
            "echo '0x100' > bcdDevice",
            f"echo '{vendor_id}' > idVendor",
            f"echo '{product_id}' > idProduct",
            f"mkdir functions/{self.gadget}",
            "sync",
            f"mkdir {self.gadget_configs}",
            f"mkdir -p {self.strings_path}",
            f"echo 'xxxxxxxxxxxx' > {self.strings_path}serialnumber",
            f"echo '{manufacture}' > {self.strings_path}manufacturer",
            f"echo {self.platform} > {self.strings_path}/product",
        ]
        self.console.runcmd_list(cmdlist)

        functions_mass_storage = "functions/mass_storage.ms0/lun.0/"
        if "mass_storage" in test:
            cmdlist = [
                f"echo /tmp/mydev > {functions_mass_storage}file",
                f"echo 1 > {functions_mass_storage}removable",
                "sync",
            ]
            self.console.runcmd_list(cmdlist)

        cmdlist = [
            f"echo 0x00 > {self.gadget_configs}MaxPower",
            f"echo 0xC0 > {self.gadget_configs}bmAttributes",
            f"ln -s functions/{self.gadget}/{self.gadget_configs}",
        ]
        self.console.runcmd_list(cmdlist)
        self.console.runcmd(
            f"echo {usb_node} > UDC",
            expected=["gadget: high-speed config", "gadget: super-speed config"],
            wait_for_prompt=False,
        )

        if "ethernet" in test:
            self.console.runcmd("ifconfig -a", expected="usb0")
        elif "serial" in test:
            self.console.runcmd("ls /dev/tty*", expected="/dev/ttyGS0")

    def mass_storage_hdparm(self, usbdev, host_terminal):
        hdparm_cmd = f"hdparm -tT /dev/{usbdev}"
        host_terminal.runcmd(
            f"sudo {hdparm_cmd}", expected="Timing buffered disk reads"
        )

    def get_mass_storage_device(self, host_terminal, vendor_id, product_id):
        host_terminal.runcmd("ls /dev/sd*")
        devices = host_terminal.output().split("\r\n")
        for device in devices:
            dev = re.search("/dev/([s][d].+)", device)
            if dev:
                dev = dev.group(1)
                host_terminal.runcmd(f"udevadm info --query=all " f"--name={dev}")
                if (
                    "ID_BUS=usb" in host_terminal.output()
                    and f"ID_VENDOR_ID={vendor_id}" in host_terminal.output()
                    and f"ID_MODEL_ID={product_id}" in host_terminal.output()
                ):
                    return dev

    def ethernet_gadget_ping(
        host_terminal,
        eth_device,
        eth_target_ip="192.168.1.1",
        eth_host_ip="192.168.1.4",
    ):
        eth_up = f"ifconfig usb0 down; ifconfig usb0 {eth_target_ip} up"
        self.console.runcmd(eth_up)
        host_terminal.runcmd("ifconfig -a")
        host_terminal.runcmd(
            f"sudo ifconfig {eth_device} {eth_host_ip} up;" f"ifconfig {eth_device}"
        )
        host_terminal.runcmd(f"ping {eth_target_ip} -c 4", expected="0% packet loss")
        log.info("ping from host to target is success")
        self.console.runcmd("ping {eth_host_ip} -c 4", expected="0% packet loss")
        log.info("ping from target to host is success")

    def serial_gadget_text_transfer(serial_device, host_terminal):
        temp_file = "/tmp/temp.txt"
        log.info(f"serial gadget device is {serial_device}")
        host_terminal.runcmd(f"head -2 {serial_device} > {temp_file} &")
        self.console.runcmd("echo 'Hello' > /dev/ttyGS0 & sleep 5")
        host_terminal.runcmd(f"sleep 5; cat {temp_file}", expected="Hello")
        self.console.runcmd(f"head -2 /dev/ttyGS0 > {temp_file} &")
        host_terminal.runcmd(f"echo 'Hiii' > {serial_device} & sleep 5")
        self.console.runcmd(f"sleep 5; cat {temp_file}", expected="Hiii")
        self.console.runcmd(f"rm {temp_file}")
        log.info("Host and target communicated successfully through usb serial gadget")

    def get_gadget_device(
        self, test_case, host_terminal, vendor_id="0x0781", product_id="0x0104"
    ):
        host_terminal.runcmd("lsusb", expected=f"{vendor_id}r'':{product_id}")
        host_terminal.runcmd("dmesg | tail -n 10")
        if test_case == "mass_storage":
            usbdev = self.get_mass_storage_device(vendor_id, product_id)
            log.info(f"mass storage gadget device is " f"{usbdev}")
            return usbdev
        elif test_case == "ethernet":
            eth_device = (
                host_terminal.output()
                .partition(": register 'cdc_ether'")[0]
                .split()[-1]
            )
            log.info(f"ethernet gadget device is " f"{eth_device}")
            return eth_device
        elif test_case == "serial":
            serial_device = (
                host_terminal.output().partition(": USB ACM device")[0].split()[-1]
            )
            serial_device = f"/dev/{serial_device}"
            log.info(f"serial gadget device is " f"{serial_device}")
            return serial_device
