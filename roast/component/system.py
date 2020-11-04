#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from abc import ABCMeta, abstractmethod


class SystemBase(metaclass=ABCMeta):
    """Base class for System component plugins"""

    def __init__(self, config):
        self.config = config

    @abstractmethod
    def configure(self):
        """Abstract class method to configure the System component"""

    @abstractmethod
    def build(self):
        """Abstract class method to build the System component"""
