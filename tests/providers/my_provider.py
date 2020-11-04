#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from mimesis import BaseDataProvider


class MyProvider(BaseDataProvider):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    class Meta:
        name = "my_provider"

    @property
    def data_file(self):
        return self._file

    @data_file.setter
    def data_file(self, file):
        self._file = file

    def foo(self):
        return "bar"
