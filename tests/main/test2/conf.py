#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from box import Box

myoverride = Box(default_box=True)

mytest = "test2"
myoverride.b.a = "hello3"
myoverride.b.b = "hello again3"

overrides = ["myoverride"]

del Box
