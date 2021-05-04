#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import sys
import pytest
from shutil import rmtree

sys.path.append(os.path.dirname(__file__))


@pytest.fixture(scope="function")
def build_dir(tmpdir):
    buildDir = os.path.join(tmpdir, "build")
    yield buildDir
    rmtree(buildDir)
