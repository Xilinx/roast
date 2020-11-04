#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import time
import re
from roast.component.petalinux import petalinux_boot
from roast.component.basebuild import Basebuild
from roast.utils import convert_list, get_var, is_file, get_base_name, get_files


def load_pdi(
    board, pdi_file=None, expected_msg="Total PLM Boot Time", expected_failures=None
) -> None:
    board.xsdb.device_program(pdi_file)
    board.serial.expect(
        expected=expected_msg,
        expected_failures=expected_failures,
        err_index=len(convert_list(expected_failures)),
    )


def linux_login_cons(
    cons, user="root", password="root", login=True, timeout=500
) -> None:
    """This Function is to login on target linux
    Parameters:
        cons - console was acquired serial or qemu instance.
        user - userid for target login
        password - password to login on target
        login - False flag will look for auto login
    """
    if login:
        cons.expect(expected="login:", timeout=timeout)
        cons.sendline("\r\n")
        cons.expect(expected="login:")
        cons.runcmd(user, expected="Password:")
        cons.runcmd(cmd=password, expected="~# ")
    else:
        cons.expect(expected="~# ", timeout=timeout)
    cons.prompt = r"root(.*?)# "
    cons.runcmd(r"PS1='\u:\t:\w\$ '", timeout=10)
    cons._setup_init()
    cons.exit_nzero_ret = True


def is_linux_cons(linuxcons, prompt="# ") -> bool:
    """This Function is to login on target linux
    Parameters:
       linuxcons - linuxcons was target serial or qemu instance
    """
    ret = True
    try:
        linuxcons.sendcontrol("c")
        linuxcons.sendline("\r\n")
        linuxcons.prompt = prompt
        linuxcons.runcmd("cd", timeout=10)
        linuxcons.prompt = r"root(.*?)# "
        linuxcons.runcmd(r"PS1='\u:\t:\w\$ '", timeout=10)
        linuxcons.sync()
        linuxcons._setup_init()
        linuxcons.exit_nzero_ret = True
    except Exception as err:
        ret = False
    return ret


def uboot_login(cons, prompt="(ZynqMP>|Zynq>|U-Boot>|Versal> )") -> None:
    """This Function is to acquite uboot on target
    Parameters:
       cons - console was acquired serial or qemu instance.
    """
    cons.exit_nzero_ret = False
    cons.expect(expected="Hit any key to stop autoboot")
    cons.sendcontrol("x")
    cons.expect(expected=prompt)
    cons.prompt = prompt


def linux_login(board, user="root", password="root", timeout=500) -> None:
    linux_login_cons(board.serial, user="root", password="root", timeout=timeout)


def is_linux(board, prompt="# ") -> bool:
    ret = is_linux_cons(board.serial, prompt="# ")
    return ret


def linux(board, timeout=500) -> None:

    xsdbcon = board.xsdb
    serialcon = board.serial
    config = board.config
    images_dir = config["component_deploy_dir"]
    files = get_files(
        f"{config.rootfs_base_path}/{config.platform}",
        extension="u-boot",
        abs_path=True,
    )
    rootfs_path = "".join(files)

    load_interface = config["load_interface"]

    if load_interface == "tcl":
        xsdbcon.run_tcl(config["linux_run_tcl"])
    elif load_interface == "petalinux":
        if board.config["boottype"] == "prebuilt":
            petalinux_boot(board.config, hwserver=board.systest_host)
        elif board.config["boottype"] == "kernel":
            petalinux_boot(
                board.config,
                boottype="kernel",
                proj_path=board.config["plnx_proj_path"],
                hwserver=board.systest_host,
            )

    elif load_interface == "images":

        # Load PDI
        load_pdi(board, board.config["pdi_file"])

        # select A72 and rst proc
        xsdbcon.set_proc("a72_0")
        xsdbcon.rst_proc()
        time.sleep(5)

        # Load kernel
        xsdbcon.load_data(images_dir + "Image", config["kernel_loadaddr"], timeout=400)
        time.sleep(1)

        # Load DTB
        xsdbcon.load_data(
            images_dir + config["system_dtb"], config["dtb_loadaddr"], timeout=400
        )
        time.sleep(1)

        # Load ROOTFS
        xsdbcon.load_data(rootfs_path, config["rootfs_loadaddr"], timeout=1200)
        time.sleep(1)

        # Load Boot.scr
        xsdbcon.load_data(config["boot_scr_path"], config["boot_scr_loadaddr"])
        time.sleep(1)

        # Start Execution
        xsdbcon.runcmd("con")

    # Wait for Linux console
    linux_login(board, timeout=timeout)
    board.is_linux = True


def copy_init_files(board):
    # Copy init files after boot.
    if board.first_boot:
        for dst_path, src_files in (board.config["board_init_files"]).items():
            for src_file in src_files:
                board.config["tmp_value"] = src_file
                # Check if file is present on host machine
                if not is_file(board.config["tmp_value"]):
                    print(f"ERROR: No Such File: {board.config['tmp_value']}")
                    raise OSError
                board.put(board.config["tmp_value"], dst_path)
                # Check if file is tar, then extract it with -C dst_path
                f_name = get_base_name(board.config["tmp_value"])
                if re.search(r"\.tar", f_name):
                    board.serial.runcmd(f"cd {dst_path}")
                    board.serial.runcmd(f"tar xvf {f_name}")
        board.serial.runcmd("cd")
        board.first_boot = False


def linuxcons(config, board_session, timeout=1000):
    board = board_session
    bb = Basebuild(config, setup=False)
    bb.configure()
    board.config = config

    if is_linux(board):
        board.is_linux = True
    else:
        board.is_linux = False
        board.target_ip = None

    pre_boot = get_var(config, "pre_boot")
    if pre_boot:
        board.is_linux = True

    # Check for board live status
    if board.is_linux:
        board.invoke_xsdb = False
        board.invoke_hwserver = False
        board.reboot = False
        if board.serial:
            board.serial.mode = False
        board.start()
        if not is_linux(board):
            raise Exception("ERROR: No linux prompt")

    elif not pre_boot:
        # boot till linux
        board.is_linux = False
        board.invoke_xsdb = True
        board.invoke_hwserver = True
        board.reboot = True
        board.first_boot = True
        board.start()
        linux(board, timeout)

    copy_init_files(board)
    return board
