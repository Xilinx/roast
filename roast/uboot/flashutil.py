#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

"""
This module holds  Flash utils class. It contails all Flash util operations.

Author: PavanKumar Vemireddy Reddy <pavankumar.vemireddy.reddy@xilinx.com>
"""

from roast.component.board.boot import load_pdi, uboot_login
from roast.uboot import flashsubsystems as fs
import re, os


class Flashutil:

    DDR_ADDR = "0x100000"  # DDR address to be used to load image for flash write

    def __init__(
        self,
        config,
        board,
        flash_type="sflash",
        instance=0,
        type="raw",
        uboot_load=True,
    ):
        self.config = config
        self.board = board
        self.console = board.serial
        self.xsdb = board.xsdb
        self.instance = instance
        self.uboot_load = uboot_load
        self.flash_type = flash_type
        self.__setup__()

    def __setup__(self):
        if self.uboot_load:
            load_pdi(self.board, self.config["uboot_pdi"])
            uboot_login(self.console)
        if self.flash_type == "sflash":
            self.flashdev = fs.SerialFlash(self.console)
        elif self.flash_type == "mmc":
            self.flashdev = fs.Mmc(self.console, instance=self.instance)
        elif self.flash_type == "fat":
            self.flashdev = fs.Fat(
                self.config, self.console, self.xsdb, instance=self.instance
            )

    def _get_len(self, pdi_name):
        """Function to calculate length of pdi

        Args:
            pdi_name(str): name of the pdi to calculate size

        Note:
            It will take care of flash type
        """
        len = os.stat(pdi_name).st_size
        if self.flash_type == "sflash" or self.flash_type == "fat":
            return hex(len)
        elif self.flash_type == "mmc":
            return hex((len // 512) + 1)

    def write_image(self, pdi_image, offset=0):
        """Function to write image to specified flash device

        Args:
            pdi_name(str): name of the pdi to load into flash device
            offset(int, optional): offset of flash device where to write data
        """
        self.xsdb.set_proc("versal")
        self.xsdb.runcmd(f"dow -data -force {pdi_image} {self.DDR_ADDR}")
        pdi_len = self._get_len(pdi_image)
        self.flashdev.erase(pdi_len, offset=offset)
        self.flashdev.write(self.DDR_ADDR, pdi_len, offset=offset)

    @classmethod
    def from_bootmode(cls, config, board, bootmode, uboot_load=True):
        """Altenative constructor, Creates class object from bootmode specified

        Args:
            config(obj): configuration object
            board(obj): board object
            bootmode(str): Specifies in which mode the device has to boot
                            Ex: qspi32,dqspi32,ospi,emmc,sd0,sd1_ls
            prompt(str): prompt that has to used
            uboot_load(bool, optional): Specify to load or not the uboot
        Note:
            It will take of flash type
        """
        if re.search("qspi", bootmode) or re.search("ospi", bootmode):
            return cls(config, board, flash_type="sflash", uboot_load=uboot_load)
        elif re.search("sd", bootmode):
            if re.search("raw", bootmode):
                return cls(
                    config,
                    board,
                    flash_type="mmc",
                    instance=0,
                    type="raw",
                    uboot_load=uboot_load,
                )
            else:
                return cls(
                    config,
                    board,
                    flash_type="fat",
                    instance=0,
                    type="fat",
                    uboot_load=uboot_load,
                )
        elif re.search("mmc", bootmode):
            if re.search("raw", bootmode):
                return cls(
                    config,
                    board,
                    flash_type="mmc",
                    instance=1,
                    type="raw",
                    uboot_load=uboot_load,
                )
            else:
                return cls(
                    config,
                    board,
                    flash_type="fat",
                    instance=1,
                    type="fat",
                    uboot_load=uboot_load,
                )
        else:
            raise ("Please selecte valid bootmode ")
