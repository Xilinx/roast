#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import pytest
from roast.providers.randomizer import Randomizer
from tests.providers import MyProvider


@pytest.fixture
def r():
    def _r(seed=0):
        randomizer = Randomizer(seed=seed)
        randomizer.add_provider(MyProvider)
        return randomizer

    return _r


def test_randomizer_provider(r):
    randomizer = r()
    randomizer.my_provider.data_file = "myfile.json"
    assert randomizer.my_provider.data_file == "myfile.json"
    assert randomizer.my_provider.foo() == "bar"


def test_randomizer_fixed_seed(r):
    values = []
    seed = 8195374381
    for _ in range(1000):
        randomizer = r(seed)
        values.append(randomizer.choice(range(1000)))
    assert set(values) == {261}
