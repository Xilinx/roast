#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from itertools import product
import pytest
from mimesis import BaseDataProvider, BaseProvider
from roast.providers.randomizer import Randomizer


class Provider1(BaseDataProvider):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    class Meta:
        name = "my_provider"

    @staticmethod
    def one():
        return 1


class Provider2(BaseProvider):
    @staticmethod
    def two():
        return 2


class Provider3(object):
    @staticmethod
    def empty():
        ...


@pytest.fixture
def r():
    def _r(seed=0):
        randomizer = Randomizer(seed=seed)
        return randomizer

    return _r


def test_randomizer_provider(r):
    randomizer = r()
    randomizer.add_providers(Provider1, Provider2)
    assert dir(randomizer) == ["choice", "my_provider", "provider2"]
    randomizer.my_provider._datafile = "myfile.json"
    assert randomizer.my_provider._datafile == "myfile.json"
    assert randomizer.my_provider.one() == 1
    assert randomizer.provider2.two() == 2
    with pytest.raises(TypeError):
        randomizer.add_providers(Provider3)
    with pytest.raises(TypeError):
        randomizer.add_providers(3)


def test_randomizer_fixed_seed(r):
    values = []
    seed = 8195374381
    for _ in range(1000):
        randomizer = r(seed)
        values.append(randomizer.choice(range(1000)))
    assert set(values) == {261}


def test_randomizer_seeded_shuffle(r):
    values = []
    seed = 8195374381
    for _ in range(1000):
        randomizer = r(seed)
        a = [1, 2, 3, 4, 5, 6]
        randomizer.random.shuffle(a)
        if a not in values:
            values.append(a)
    assert len(values) == 1
    assert values[0] == [4, 5, 1, 6, 2, 3]


def test_randomizer_seeded_product_shuffle(r):
    combinations = []
    speed = [10, 100, 1000]
    duplex = ["half", "full"]
    seed = 8195374381
    randomizer = r(seed)
    combination = list(product(speed, duplex))
    for _ in range(len(combination)):
        combinations.append(combination[:])
        randomizer.random.shuffle(combination)
    # fmt: off
    assert combinations == [
        [(10, 'half'), (10, 'full'), (100, 'half'), (100, 'full'), (1000, 'half'), (1000, 'full')],
        [(100, 'full'), (1000, 'half'), (10, 'half'), (1000, 'full'), (10, 'full'), (100, 'half')],
        [(1000, 'half'), (100, 'half'), (10, 'half'), (100, 'full'), (1000, 'full'), (10, 'full')],
        [(10, 'half'), (1000, 'half'), (100, 'half'), (10, 'full'), (100, 'full'), (1000, 'full')],
        [(100, 'full'), (1000, 'half'), (10, 'half'), (1000, 'full'), (100, 'half'), (10, 'full')],
        [(1000, 'half'), (100, 'half'), (100, 'full'), (10, 'half'), (10, 'full'), (1000, 'full')],
    ]
    # fmt: on
