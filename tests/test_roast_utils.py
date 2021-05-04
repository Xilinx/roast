#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from roast.utils.roast_utils import overrides as overrides_func
from box import Box


def test_generate_conf_override_func():
    config = Box(default_box=True, box_dots=True)
    config.a.a = "A.A"
    config.a.b = "A.B"
    config.zcu102.a.a = "ZCU102.A.A"
    config.zcu102.a.b = "ZCU102.A.B"
    override = "zcu102"
    config = overrides_func(config, override)
    assert config["a.a"] == "ZCU102.A.A"
    assert config["a.b"] == "ZCU102.A.B"


def test_generate_conf_override_list_func(request):
    config = Box(default_box=True, box_dots=True)
    config.a.a = "A.A"
    config.a.b = "A.B"
    config.b.a = "B.A"
    config.b.b = "B.B"
    config.zcu102.a.a = "ZCU102.A.A"
    config.zcu102.a.b = "ZCU102.A.B"
    config.zynq.b.a = "ZYNQ.A.A"
    config.zynq.b.b = "ZYNQ.A.B"
    overrides = ["zynq", "zcu102"]
    config = overrides_func(config, overrides)
    assert config["a.a"] == "ZCU102.A.A"
    assert config["a.b"] == "ZCU102.A.B"
    assert config["b.a"] == "ZYNQ.A.A"
    assert config["b.b"] == "ZYNQ.A.B"
