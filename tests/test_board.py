#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import socket
import pytest
from roast.component.board.board import Board
from roast.utils import register_plugin


@pytest.fixture
def b():
    name = "dummy_board"
    register_plugin(name, "board", "tests.test_plugin:DummyBoard")
    return Board(board_type=name)


def test_board_interface(b, mocker):
    assert isinstance(b, Board)
    assert b.driver.config == {}
    b.start()
    b.put("a", "b")
    b.get("c", "d")
    b.reset()
    assert b.driver.start
    assert b.driver.put_src_file == "a"
    assert b.driver.put_dest_path == "b"
    assert b.driver.get_src_file == "c"
    assert b.driver.get_dest_path == "d"
    assert b.driver.reset
