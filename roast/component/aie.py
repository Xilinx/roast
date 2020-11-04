#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import time
import sys
from roast.component.board.boot import load_pdi, is_linux, linuxcons
from roast.utils import is_file, copyDirectory
from roast.component.cardano import check_cardano


def run_plm(
    board,
    expected_msg="Total PLM Boot Time",
    expected_failures=None,
    load_aie_pdi=False,
):
    if load_aie_pdi:
        load_pdi(
            board, pdi_file=board.config["aie_pdi"], expected_failures=expected_failures
        )
    load_pdi(board, expected_msg=expected_msg, expected_failures=expected_failures)


def run_std_app(board, procname, load_boot_pdi=False):
    load_pdi(board, pdi_file=board.config["aie_pdi"])
    if load_boot_pdi:
        load_pdi(board, expected_msg="SBI PDI Load: Done")
    board.xsdb.set_proc(procname)
    board.xsdb.rst_proc()
    time.sleep(5)
    aie_elf = f"{board.config['imagesDir']}/aie_control.elf"
    if not is_file(aie_elf):
        print(f"ERROR: No Such File {aie_elf}", file=sys.stderr)
        raise Exception("Build test Failed")
    board.xsdb.load_elf(f"{board.config['imagesDir']}/aie_control.elf")
    board.xsdb.runcmd("con")


def run_aie_demo(board):
    board.serial.prompt = "# "
    rst_list = [
        "devmem 0xF70A000C w 0xF9E8D7C6",
        "devmem 0xF70A0000 w 0x4000000",
        "devmem 0xF70A0004 w 0x40381B1",
        "devmem 0xF70A0000 w 0x4000000",
        "devmem 0xF70A0004 w 0x00381B1",
        "devmem 0xF70A000C w 0x12341234",
    ]

    board.serial.runcmd_list(rst_list)
    board.serial.runcmd("cd /lib/firmware/aie")
    board.serial.runcmd(
        "aie-matrix-multiplication",
        expected="Success!",
        expected_failures="ERROR: XGeMM Failed!",
        timeout=600,
    )


def run_linux_app(board):
    test = board.config["test"]
    src_file = f"{board.config['imagesDir']}/deploy_artifacts.tar.xz"
    if not is_file(src_file):
        print(f"ERROR: No Such File {src_file}", file=sys.stderr)
        raise Exception("Build test Failed")
    board.put(src_file, "~/")
    # board.serial.terminal.interact()

    board.serial.runcmd(f"mkdir -p ~/{test}")
    cmd_list = [f"tar xvf deploy_artifacts.tar.xz -C {test}/", f"cd {test}"]
    board.serial.runcmd_list(cmd_list)
    # Load pdi through fpga manager if present
    if board.config["cardano_app"]:
        # Reset AIE Array
        board.serial.runcmd("../reset-aie.run", expected="Resetting AIE Array Done.")

        board.serial.runcmd("echo 1 >  /sys/class/fpga_manager/fpga0/flags")
        board.serial.runcmd("cp boot.pdi /lib/firmware/")
        board.serial.runcmd(
            "echo boot.pdi > /sys/class/fpga_manager/fpga0/firmware",
            expected=["Subsystem PDI Load: Done"],
        )

    wait_for_prompt = False if test == "clock_gating" else True
    try:
        board.serial.runcmd(
            "./aie_control.run",
            wait_for_prompt=wait_for_prompt,
            expected=["SUCCESS", "Killed", "Kernel panic"],
            expected_failures=["FAILED", "Segmentation fault", "Aborted"],
        )
    except Exception as err:
        # Reset console to normal state for consecutive tests
        is_linux(board)
        assert False, err


def copy_linux_test_images(config, test):
    linux_images = f"{config['buildDir']}/{config['machine']}/{test}/linux/images/"
    copyDirectory(linux_images, config["imagesDir"])
    check_cardano(config)


def petalinux_aie_boot(config, board_session, boottype):
    config["plnx_proj"] = config["PLNX_BSP"]
    config["load_interface"] = "petalinux"
    config["boottype"] = boottype
    config["board_init_files"] = {}
    if boottype == "kernel":
        config[
            "plnx_proj_path"
        ] = f"{config['buildDir']}/{config['machine']}/petalinux/default_build/work/{config['PLNX_BSP']}"

    board_session.invoke_xsdb = False
    board = linuxcons(config, board_session)
    return board
