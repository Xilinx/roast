#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

try:
    # For python 3.8 and later
    import importlib.metadata as importlib_metadata
except ImportError:
    # For everyone else
    import importlib_metadata

import pytest
from stevedore import ExtensionManager
from roast.utils import register_plugin
from roast.serial import SerialBase
from roast.component.board.board import BoardBase


class DummySerial(SerialBase):
    def __init__(self, config):
        super().__init__(config)

    def _configure(self):
        self.hostname = "hostname"
        self.configure = True

    def _connect(self):
        self.connect = True

    def exit(self):
        self.exit = True


class DummyBoard(BoardBase):
    def __init__(self):
        super().__init__()

    def start(self):
        self.start = True

    def put(self, src_file, dest_path):
        self.put_src_file = src_file
        self.put_dest_path = dest_path

    def get(self, src_file, dest_path):
        self.get_src_file = src_file
        self.get_dest_path = dest_path

    def reset(self):
        self.reset = True


def test_register_plugin():
    namespace = "roast.serial"
    name = "dummy_serial"
    register_plugin(name, "serial", "test_plugin:DummySerial")
    e = ExtensionManager(namespace)
    serial_entries = [
        entry_point.name for entry_point in e.ENTRY_POINT_CACHE.get(namespace)
    ]
    assert name in serial_entries

    namespace = "roast.board"
    name = "dummy_board"
    register_plugin(name, "board", "test_plugin:DummyBoard")
    e = ExtensionManager(namespace)
    board_entries = [
        entry_point.name for entry_point in e.ENTRY_POINT_CACHE.get(namespace)
    ]
    assert name in board_entries


def test_register_plugin_exception():
    with pytest.raises(Exception, match="not supported"):
        register_plugin("", "", "")
