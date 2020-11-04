#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import pytest
from shutil import rmtree


@pytest.fixture(scope="function")
def build_dir(tmpdir):
    buildDir = os.path.join(tmpdir, "build")
    yield buildDir
    rmtree(buildDir)
