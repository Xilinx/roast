#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import sys
import subprocess
import datetime
from roast.utils import *  # pylint: disable=unused-wildcard-import
from roast.component.system import SystemBase


class Basebuild(SystemBase):
    def __init__(self, config, setup: bool = True):
        super(Basebuild, self).__init__(config)
        self.setup = setup

    def configure(self):
        self.src = self.config["test_path"]
        self._setup_wsDir()
        self.workDir = os.path.join(self.wsDir, "work")
        self.logDir = os.path.join(self.wsDir, "logs")
        self.imagesDir = os.path.join(self.wsDir, "images")
        self._setup_config()
        self._setup_dirs()

    def _setup_config(self):
        self.config["wsDir"] = self.wsDir
        self.config["workDir"] = self.workDir
        self.config["logDir"] = self.logDir
        self.config["imagesDir"] = self.imagesDir

    def _setup_wsDir(self):
        self.wsDir = self.config["buildDir"]
        # Add base params
        if self.config["base_params"]:
            self.wsDir = os.path.join(self.wsDir, *self.config["base_params"])

        self.config["base_ws_dir"] = self.wsDir
        # Add test path
        self.wsDir = os.path.join(self.wsDir, *self.config["test_path_list"])
        self.config["test_base_ws_dir"] = self.wsDir

        # Add test params
        if self.config["params"]:
            self.wsDir = os.path.join(self.wsDir, *self.config["params"])

    def _cp_src_to_work(self):
        if is_dir(self.src):
            copyDirectory(self.src, self.workDir)

    def _setup_dirs(self):
        if self.setup:
            reset(self.wsDir)
        mkdir(self.workDir)
        mkdir(self.logDir)
        mkdir(self.imagesDir)
        os.chdir(self.workDir)  # FIXME: libraries shouldn't change working directory
        if self.setup:
            # Copy test files
            # Iterate from last param till test_path.
            params_list = self.config["params"]
            while True:
                self.src = os.path.join(self.config["test_path"], *params_list)
                if is_dir(self.src):
                    copyDirectory(self.src, self.workDir)
                    break
                if params_list:
                    params_list.pop()
                else:
                    break

    def build(self):
        raise NotImplementedError
