#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from roast.utils import get_combinations
import re


class TestCollect:
    def __init__(self):
        self.tests = {}

    def add_tests(self, **kwargs):
        combinations = self._get_test_combinations(**kwargs)
        self.tests.update(combinations)

    def remove_tests(self, **kwargs):
        combinations = self._get_test_combinations(**kwargs)
        for item in combinations.keys():
            self.tests.pop(item)

    def test_map(self, tests_list, parameters, scenario=[]):
        for test in tests_list:
            test = [test]
            test.extend(scenario)
            self.tests[tuple(test)] = parameters

    def _get_test_combinations(self, **kwargs):
        keys = kwargs.keys()
        values = list(kwargs.values())
        combinations = {}
        # FIXME: Empty list is not handled
        for combination in get_combinations(values):
            key = "-".join([myval for myval in combination if myval])
            combinations[key] = dict(zip(keys, combination))
        return combinations

    def get_tests(self, silent_discard=False, sort=False):
        ret = list(self.tests.keys())
        if not ret and not silent_discard:
            raise Exception("ERROR: Empty tests list")
        if sort:
            return sorted(ret)
        else:
            return ret

    def get_test_params(self, test_name):
        return self.tests[test_name]  # returns dictinary with key value pairs


def get_cmdl_machine_opt():
    import pytest

    machine = pytest.machine
    if machine:
        return machine[0].split(",")
    else:
        return None
