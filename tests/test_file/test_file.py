#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
from roast.utils import read_json, write_json


def test_json_read(tmpdir):
    json_file = os.path.join(os.path.dirname(__file__), "test.json")
    my_dict = read_json(json_file)
    assert my_dict == {
        "int": 10,
        "hex": "0x0C",
        "octal": "0o20",
        "bin": "0b10000",
        "string": "value",
        "scientific": "8.000000e+02",
    }
    my_dict = read_json(json_file, decode_numbers=True)
    assert my_dict == {
        "int": 10,
        "hex": 12,
        "octal": 16,
        "bin": 16,
        "string": "value",
        "scientific": 800.0,
    }
