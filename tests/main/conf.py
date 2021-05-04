#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from box import Box

mysubtree = Box(default_box=True)

version = "2019.2"
mylist = ["c", "d"]
mytest = ""
mysubtree.b.a = "hello2"
mysubtree.b.b = "hello again2"

del Box
