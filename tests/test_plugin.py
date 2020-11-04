#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import pkg_resources
import pytest
from roast.utils import register_plugin


class DummyPlugin:
    def __init__(self):
        pass


def test_register_plugin():
    location = __file__
    name = "dummy_serial"
    register_plugin(location, name, "serial", "tests.test_plugin:DummyPlugin")
    serial_entries = [
        entry_point.name
        for entry_point in pkg_resources.iter_entry_points("roast.serial")
    ]
    assert name in serial_entries

    name = "dummy_board"
    register_plugin(location, name, "board", "tests.test_plugin:DummyPlugin")
    board_entries = [
        entry_point.name
        for entry_point in pkg_resources.iter_entry_points("roast.board")
    ]
    assert name in board_entries


def test_register_plugin_exception():
    with pytest.raises(Exception, match="not supported"):
        register_plugin("", "", "", "")
