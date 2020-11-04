#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from abc import ABCMeta, abstractmethod


class TestSuiteBase(metaclass=ABCMeta):
    """Base class for Test Suite component plugin"""

    def __init__(self, config):
        self.config = config

    @abstractmethod
    def configure(self):
        """Abstract class method to configure the TestSuite component"""

    @abstractmethod
    def build(self):
        """Abstract class method to build the TestSuite component"""

    @abstractmethod
    def deploy(self):
        """Abstract class method to deploy the TestSuite component"""

    @abstractmethod
    def run(self):
        """Abstract class method to run the TestSuite component"""
