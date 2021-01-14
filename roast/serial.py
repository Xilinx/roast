#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from abc import ABCMeta, abstractmethod
from stevedore import driver


class Serial:
    def __init__(self, serial_type: str, config, **kwargs) -> None:
        self._serial_mgr = driver.DriverManager(
            namespace="roast.serial",
            name=serial_type,
            invoke_on_load=True,
            invoke_args=(config,),
            invoke_kwds=kwargs,
        )

    @property
    def driver(self) -> driver:
        return self._serial_mgr.driver

    def exit(self) -> None:
        self.driver.exit()


class SerialBase(metaclass=ABCMeta):
    def __init__(self, config) -> None:
        self.config = config

    @abstractmethod
    def exit(self) -> None:
        """Release connection."""
