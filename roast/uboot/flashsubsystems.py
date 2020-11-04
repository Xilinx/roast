#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

"""
This module holds Serial flash class. It contails all serial flash operations.

Author: PavanKumar Vemireddy Reddy <pavankumar.vemireddy.reddy@xilinx.com>
"""
import re
from math import ceil


class SerialFlash:
    # TODO
    # Make use of flash pattern and get all attributes dynamically from flash
    FLASH_PATTERN = re.compile(
        r"SF: Detected (.*?) with page size (.*?), erase \
        size (.*?), total (.*?)$"
    )
    # 512 Kb max erase size in general flashes
    ERASE_SIZE = 512 * 1024

    def __init__(self, console):
        self.console = console
        self._probe()

    def _probe(self, cs=0, hz=0, mode=0):
        """Function to probe Serial flash

        Args:
            cs(int, optional): chipselect
            hz(int, optional): Frequency in Hertz
            mode(int, optional): Mode bit
        """
        self.console.runcmd(f"\r\n")
        self.console.runcmd(f"sf probe {cs} {hz} {mode}", expected="SF: Detected")

    def read(self, addr, length, offset=0):
        """ Function to read 'length' of bytes starting from 'offset' to \
            memory at 'addr'

        Args:
            addr(int): Memory address to load read data
            length(int): length of bytes to be read
            offset(int, optional): offset of flash from where to read data
        """
        self.console.runcmd(f"sf read {addr} {offset} {length}", expected="OK")

    def write(self, addr, length, offset=0):
        """ Function to write 'length' of bytes from  memory at 'addr' to \
            flash at 'offset'

        Args:
            addr(int): Memory address from where to write data
            length(int): length of bytes to be write
            offset(int, optional): offset of flash to where write data
        """
        self.console.runcmd(
            f"sf write {addr} {offset} {length}", expected="Written: OK", timeout=600
        )

    def erase(self, length, offset=0):
        """ Function to erase 'length' of bytes from flash 'offset'

        Args:
            length(int): length of bytes to be erased
            offset(int, optional): offset of flash from where erase start

        Note:
            size of erase should be in multiples of erase block size so it \
            will automatically erase size will ceil to nearest erase block size
        """
        length = self.ERASE_SIZE * ceil(int(length, 16) / self.ERASE_SIZE)
        length = hex(length)
        self.console.runcmd(f"sf erase {offset} {length}", expected="OK")

    def update(self, addr, length, offset=0):
        """ Function to erase and write 'length' of bytes from  memory at \
            'addr' to flash at 'offset'

        Args:
            addr(int): Memory address from where to write data
            length(int): length of bytes to be write
            offset(int, optional): offset of flash to where write data
        """
        self.console.runcmd(f"sf update {addr} {offset} {length}")


class Mmc:
    def __init__(self, console, instance=0):
        self.console = console
        self.instance = instance
        self._setup()

    def _setup(self):
        self.console.runcmd(f"mmc dev {self.instance}", expected="OK")

    def read(self, addr, length, offset=0):
        """ Function to read 'length' of bytes starting from 'offset' to \
            memory at 'addr'

        Args:
            addr(int): Memory address to load read data
            length(int): length of bytes to be read
            offset(int, optional): offset of mmc from where to read data
        """
        self.console.runcmd(f"mmc read {addr} {offset} {length}", expected="OK")

    def write(self, addr, length, offset=0):
        """ Function to write 'length' of bytes from  memory at 'addr' to \
            mmc at 'offset'

        Args:
            addr(int): Memory address from where to write data
            length(int): length of bytes to be write
            offset(int, optional): offset of mmc to where write data
        """
        self.console.runcmd(f"mmc write {addr} {offset} {length}", expected="OK")

    def erase(self, length, offset=0):
        """Function to erase 'length' of bytes from flash 'offset'

        Args:
            length(int): length of bytes to be erased
            offset(int, optional): offset of flash from where erase start
        """
        self.console.runcmd(f"mmc erase {offset} {length}", expected="OK")

    def switch(self, instance):
        """Function to switch instance of mmc device'

        Args:
            instance(int): instance to which we need to switch
        """
        self.console.runcmd(f"mmc dev {instance}", expected="OK")

    def hwpartition(self):
        pass

    def setdsr(self):
        pass


class Fat:

    BIN_FILE = "BOOT.BIN"

    def __init__(self, config, console, xsdb, instance=0):
        self.config = config
        self.console = console
        self.xsdb = xsdb
        self.instance = instance
        self._setup()

    def _setup(self):
        """ Check the flash whether its formatted to FAT32 or Not and format \
            it if its not Currently there are no commands available in uboot \
            to format Flash So using a tcl file to do that
        """
        try:
            self.console.runcmd(
                f"fatinfo mmc {self.instance}", expected="Filesystem: FAT32"
            )
        except:
            self.xsdb.runcmd("set argv [list %s ]" % (self.instance))
            self.xsdb.run_tcl(self.config["fat_formatter"])
            self.console.expect(
                expected="Successfully Formatted", wait_for_prompt=False
            )

    def write(self, addr, length, offset=0):
        """ Function to write 'length' of bytes from  memory at 'addr' to \
            mmc at 'offset'

        Args:
            addr(int): Memory address from where to write data
            length(int): length of bytes to be write
            offset(int, optional): offset of mmc to where write data
        """
        self.console.runcmd(
            f"fatwrite mmc {self.instance} {addr} \
            {self.BIN_FILE} {length}",
            expected="bytes written",
        )

    def erase(self, length, offset=0):
        """Dummy function to sync with other flash classes"""
        pass

    def createdir(self):
        pass
