#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import socket
import time
from roast.utils import get_var, has_key
from roast.serial import Serial
from roast.component.xsdb.xsdb import Xsdb


def is_sd(board):
    """This method checks if sd is present
    Parameters:
        board : object of Board class
    """
    linuxcons = board.serial
    linuxcons.runcmd("ls /var/log", expected="\r\n")
    if "dmesg" not in linuxcons.output():
        linuxcons.runcmd("dmesg >> /var/log/dmesg")
    linuxcons.runcmd("cat /var/log/dmesg | grep 'sdhci' | wc -l", expected="\r\n")
    sdstring = linuxcons.output()
    if int(sdstring) >= 1:
        return True
    else:
        return False


def find_sdmount_point(board, boot_device):
    """This method finds the sd mount point and returns sd device
    Parameters:
        board : object of Board class
    """
    linuxcons = board.serial
    linuxcons.runcmd("ls -l /dev | grep mmcblk", err_msg="No SD Device found")

    linuxcons.runcmd("ls /sys/class/mmc_host/", expected="\r\n")
    mmc_host_files = linuxcons.output().split()
    for mmc_host in mmc_host_files:
        mmc_host = f"/sys/class/mmc_host/{mmc_host}"
        cmd = f"echo '{mmc_host}' | cut -d '/' -f 5 | sed 's/mmc//g'"
        linuxcons.runcmd(cmd, expected="\r\n")
        sd_num = linuxcons.output()
        cmd = f"grep -irn -w -q 'MMC_TYPE={boot_device}' '{mmc_host}' ; echo $?"
        linuxcons.runcmd(cmd, expected="\r\n")
        if linuxcons.output() == "0":
            sd_device = f"/dev/mmcblk{sd_num}"
            return sd_device


def umount(linuxcons, partition):
    """This method unmounts the partition mentioned as a parameter
    Parameters:
        linuxcons : board.serial object
        partition : any partition that should be unmounted
    >>> Usage:
        partition= "/mnt"
    """
    linuxcons.runcmd(
        f"mount | grep -w {partition}", expected="\r\n", wait_for_prompt=False
    )
    linuxcons.expect(expected="# ", wait_for_prompt=False)
    if f"{partition}" in linuxcons.output():
        linuxcons.runcmd(f"umount {partition}")


def scp(board):
    """This method copies images to /mnt through scp
    Parameters:
        board : object of Board class
        images_path : image directory path from which the images should be
                      copied to /mnt
    >>> Usage:
        sd_boot_artifacts = ['boot.scr', 'BOOT.BIN', 'image.ub', 'system.dtb'
                             'rootfs.tar.gz']
    """

    board.serial.runcmd("mkdir -p /nfsroot")
    for image in board.config["sd_boot_artifacts"]:
        board.put(
            src_file=f"{board.config['images_path']}/{image}", dest_path="/nfsroot/"
        )
    board.serial.runcmd("cp /nfsroot/* /mnt/ -r")


def nfs_mount(board):
    """This method performs nfsmount based on the directory path given in
    systest_nw_shared_path and copies them to /mnt
    Parameters:
        board : object of Board class
        systest_nw_shared_path : image directory path to be mounted on SD
    >>> Usage:
        sd_boot_artifacts = ['boot.scr', 'BOOT.BIN', 'image.ub', 'system.dtb']
    """
    linuxcons = board.serial
    linuxcons.runcmd("mkdir -p /nfsroot")
    umount(linuxcons, "/nfsroot")
    ip_address = socket.gethostbyname(board.systest_host)
    linuxcons.runcmd(
        "[ ! -z $(which mount.nfs) ] && \
            chmod 755 $(which mount.nfs) || echo 'mount.nfs not found'"
    )
    cmd = f"mount -o port=2049,nolock,proto=tcp,vers=2 {ip_address}:/exports/root /nfsroot"
    linuxcons.runcmd(cmd)
    for image in board.config["sd_boot_artifacts"]:
        linuxcons.runcmd(f"cp /nfsroot/{image} /mnt")
    linuxcons.runcmd(f"sync")


def fat32(board, sd_device, partition_size="500"):
    """This method prepares SD in FAT32 format
    Parameters:
        board : object of Board class
        sd_device : the return value of find_sdmount_point
        partition_size : size of the partition to be made and default is 500
        copy_method : method in which images can be copied (nfs_mount or scp)
    >>> Usage:
        copy_method = "scp" or copy_method = "nfsmount"
    """

    linuxcons = board.serial
    umount(linuxcons, sd_device)
    umount(linuxcons, f"{sd_device}p1")
    umount(linuxcons, f"{sd_device}p2")

    cmdlist = [
        f"dd if=/dev/zero of={sd_device} bs=1024 count=4",
        f"echo -e 'p\nn\np\n1\n\n+{partition_size}M\nw\n' | fdisk {sd_device}",
        f"mkdir -p /mnt;mkfs.vfat -F 32 -n boot {sd_device}p1",
    ]
    linuxcons.runcmd_list(cmdlist)
    umount(linuxcons, "/mnt")
    cmdlist = [f"mount {sd_device}p1 /mnt", "df -h", "cd /mnt"]
    linuxcons.runcmd_list(cmdlist)

    if get_var(board.config, "copy_method") == "scp":
        scp(board)
    else:
        nfs_mount(board)

    cmdlist = ["ls -alt /mnt", "cd /", "umount /mnt", "sync"]

    linuxcons.runcmd_list(cmdlist)
    umount(linuxcons, "/nfsroot")
    linuxcons.runcmd("df -h")


def ext(board, sd_device, partition="ext4", partition_size="500", timeout=900):
    """This method prepares SD in ext format
    Parameters:
        board : object of Board class
        sd_device : the return value of find_sdmount_point
        partition_size : size of the partition to be made and default is 500
        copy_method : method in which images can be copied (nfs_mount or scp)
        partition : can take any format type (ext4, ext3 etc.,)
    >>> Usage:
            copy_method = "scp" or copy_method = "nfsmount"
    """

    linuxcons = board.serial
    umount(linuxcons, sd_device)
    umount(linuxcons, f"{sd_device}p1")
    umount(linuxcons, f"{sd_device}p2")

    cmdlist = [
        f"dd if=/dev/zero of={sd_device} bs=1024 count=4",
        f"echo -e 'n\np\n1\n\n+{partition_size}M\nn\np\n2\n\n\np\nw\n' | fdisk {sd_device}",
        f"mkfs.vfat -F 32 -n boot {sd_device}p1",
    ]

    linuxcons.runcmd_list(cmdlist)
    umount(linuxcons, f"{sd_device}p2")
    linuxcons.runcmd(f"echo y | mkfs.{partition} -L root {sd_device}p2")
    umount(linuxcons, "/mnt")
    cmdlist = [
        f"echo -e 'y\ny' | mount {sd_device}p1 /mnt",
        "df -h",
        "cd /mnt",
        "rm -rf *",
    ]
    linuxcons.runcmd_list(cmdlist)
    if get_var(board.config, "copy_method") == "scp":
        scp(board)
    else:
        nfs_mount(board)
    cmdlist = [
        "ls -alt /mnt",
        "cd /",
        "umount /mnt",
        f"echo -e 'y\ny' | mount {sd_device}p2 /mnt",
        "df -h",
        "cd /mnt",
    ]

    linuxcons.runcmd_list(cmdlist)
    copy_rootfs(board, timeout)
    cmdlist = ["ls -alt /mnt", "cd /", "umount /mnt", "sync"]

    linuxcons.runcmd_list(cmdlist)
    umount(linuxcons, "/nfsroot")
    linuxcons.runcmd("df -h")


def copy_rootfs(board, timeout):
    """This method copies rootfs tar to /mnt and then untar it.
    Parameters:
        board : object of Board class
        rootfs : rootfs filename
    >>> Usage:
        rootfs = "rootfs.tar.gz"
    """
    board.serial.runcmd("cd /mnt")
    board.serial.runcmd(f"cp /nfsroot/{board.config['rootfs']} /mnt", timeout=timeout)
    board.serial.runcmd(f"tar xvf {board.config['rootfs']}", timeout=timeout)


def zynqmp_bootmode_sd(board, boot_device):
    addr_dict = {"SD": {"0xff5e0200": "0xE100"}, "MMC": {"0xff5e0200": "0x6100"}}
    board.xsdb.set_proc("PSU")
    time.sleep(2)
    board.xsdb.write(addr_dict[boot_device])
    board.xsdb.read("0xff5e0200", args="-force")
    time.sleep(2)
    board.xsdb.set_proc("PSU")
    board.xsdb.runcmd("rst -system")
    time.sleep(2)
    board.xsdb.runcmd("con")
    time.sleep(2)


def sd_prep_fat32(board, boot_device="SD"):
    is_sd(board)
    sd_device = find_sdmount_point(board, boot_device)
    fat32(board, sd_device)


def sd_prep_ext4(board, boot_device="SD"):
    is_sd(board)
    sd_device = find_sdmount_point(board, boot_device)
    ext(board, sd_device)


def sd_boot(board, boot_device="SD"):
    board.serial.mode = True
    board.systest.reboot()
    if not board.xsdb:
        board.xsdb = Xsdb(board.config, hwserver=board.config["systest_host"])

    board.serial = Serial("systest", board.config, mode=True).driver
    if board.config["platform"] == "zynq":
        board.systest.runcmd("bootmode 'sd'")
        board.serial.mode = True
        board.systest.reset()
    elif board.config["platform"] == "zynqmp":
        if has_key(board.config, "bootmode_tcl"):
            board.xsdb.run_tcl(f"{board.config['bootmode_tcl']}")
        else:
            zynqmp_bootmode_sd(board, boot_device)

    elif board.config["platform"] == "versal":
        board.systest.runcmd("bootmode 'sd1_ls'")
