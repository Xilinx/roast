#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
from itertools import product
import pytest
from mimesis import BaseDataProvider, BaseProvider
from roast.providers.randomizer import Randomizer
from roast.exceptions import RandomizerError


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
    def _r(seed=0, randomize=True):
        randomizer = Randomizer(seed=seed, randomize=randomize)
        randomizer.datafile = os.path.join(os.path.dirname(__file__), "parameters.json")
        return randomizer

    return _r


def test_randomizer_provider(r):
    randomizer = r()
    randomizer.add_providers(Provider1, Provider2)
    assert dir(randomizer) == [
        "boolean",
        "choice",
        "choices",
        "evaluate",
        "my_provider",
        "parameters",
        "parser",
        "provider2",
        "randomize",
    ]
    randomizer.my_provider._datafile = "myfile.json"
    assert randomizer.my_provider._datafile == "myfile.json"
    assert randomizer.my_provider.one() == 1
    assert randomizer.provider2.two() == 2
    with pytest.raises(TypeError):
        randomizer.add_providers(Provider3)
    with pytest.raises(TypeError):
        randomizer.add_providers(3)


def test_randomizer_fixed_seed(r):
    choice_values = []
    choices_values = []
    seed = 8195374381
    for _ in range(1000):
        randomizer = r(seed)
        choice_values.append(randomizer.choice(range(1000)))
        choices_values.extend(randomizer.choices(range(1000)))
    assert set(choice_values) == {261}
    assert set(choices_values) == {255}


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


def test_choices_fixed_seed_weighted(r):
    seed = 8195374381
    randomizer = r(seed)
    items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    weights = [8, 3, 9, 2, 10, 1, 8, 3, 9, 2, 10, 1, 8, 3, 9, 2, 10, 1, 8, 3]
    chosen = randomizer.choices(items, weights, length=10)
    assert chosen == [5, 3, 4, 17, 11, 11, 11, 1, 1, 8]


def test_choices_fixed_seed_weighted_unique(r):
    seed = 8195374381
    randomizer = r(seed)
    items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    weights = [8, 3, 9, 2, 10, 1, 8, 3, 9, 2, 10, 1, 8, 3, 9, 2, 10, 1, 8, 3]
    chosen = randomizer.choices(items, weights, length=10, unique=True)
    assert chosen == [5, 3, 4, 17, 11, 1, 8, 19, 10, 9]


def test_choices_non_sequence_items(r):
    randomizer = r()
    with pytest.raises(TypeError):
        randomizer.choices(items=5)


def test_choice_empty_items(r):
    randomizer = r()
    with pytest.raises(ValueError):
        randomizer.choices(items=[])


def test_choice_negative_length(r):
    randomizer = r()
    with pytest.raises(ValueError):
        randomizer.choices(items=("a", "b"), length=-1)


def test_choice_insufficient_unique(r):
    randomizer = r()
    with pytest.raises(ValueError):
        randomizer.choices(items=["a", "b"], length=3, unique=True)


def test_randomizer_data(r):
    randomizer = r(seed=12345)
    assert randomizer.get_value("ip.attribute1") == 256
    assert randomizer.get_value("ip.attribute2") == 190
    assert randomizer.get_value("ip.attribute3") == 2
    assert randomizer.get_value("ip.attribute5") == 8
    assert randomizer.get_value("ip.attribute6") == 11
    assert randomizer.get_value("ip.attribute7") == 0.6
    assert randomizer.get_value("ip.attribute8") == -0.8
    assert randomizer.get_value("ip.attribute9") == -1.2


def test_bif_provider_no_randomize(r):
    randomizer = r(seed=12345, randomize=False)
    assert randomizer.get_value("ip.attribute1") == 64
    assert randomizer.get_value("ip.attribute2") == 127
    assert randomizer.get_value("ip.attribute3") == 9
    assert randomizer.get_value("ip.attribute5") == 2
    assert randomizer.get_value("ip.attribute6") == 14
    assert randomizer.get_value("ip.attribute7") == 1.4
    assert randomizer.get_value("ip.attribute8") == -1.4
    assert randomizer.get_value("ip.attribute9") == -1.6


def test_bif_provider_exception(r):
    randomizer = r(seed=12345, randomize=True)
    with pytest.raises(KeyError, match="Attribute ip.attribute0 not defined"):
        randomizer.get_value("ip.attribute0")
    with pytest.raises(KeyError, match="Attribute ip.attribute0 not defined"):
        randomizer.get_all_values("ip.attribute0")
    with pytest.raises(
        KeyError, match="For attrbiute ip.attribute4, values or range not defined"
    ):
        randomizer.get_value("ip.attribute4")
    with pytest.raises(
        KeyError, match="For attrbiute ip.attribute4, values or range not defined"
    ):
        randomizer.get_all_values("ip.attribute4")


def test_randomizer_get_all_values(r):
    randomizer = r()
    assert randomizer.get_all_values("ip.attribute1") == [32, 256, 512]
    attribute2 = list(range(0, 256))
    attribute2.remove(35)
    attribute2.remove(36)
    attribute2.remove(37)
    assert randomizer.get_all_values("ip.attribute2") == attribute2
    assert randomizer.get_all_values("ip.attribute3") == list(range(0, 128))
    attribute5 = [0, 2, 8, 10]
    assert randomizer.get_all_values("ip.attribute5") == attribute5
    assert randomizer.get_all_values("ip.attribute6") == list(range(0, 21))
    attribute7 = [0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0]
    assert randomizer.get_all_values("ip.attribute7") == attribute7
    attribute8 = [0, -0.2, -0.4, -0.6, -0.8, -1.0, -1.2, -1.4, -1.6, -1.8, -2.0]
    assert randomizer.get_all_values("ip.attribute8") == attribute8
    attribute9 = [-2.0, -1.8, -1.6, -1.4, -1.2, -1.0]
    assert randomizer.get_all_values("ip.attribute9") == attribute9


def test_randomizer_boolean(r):
    boolean_values = []
    for _ in range(100):
        randomizer = r(seed=123456789)
        boolean_values.append(randomizer.boolean())
    assert set(boolean_values) == {False}


def test_randomizer_generate_sequence(r):
    randomizer = r(seed=123456)
    assert randomizer.generate_sequence(
        "prev < current",
        ["ip.delay_500", "ip.delay_501", "ip.delay_502", "ip.delay_503"],
    ) == {
        "ip.delay_500": 57,
        "ip.delay_501": 82,
        "ip.delay_502": 87,
        "ip.delay_503": 91,
    }
    assert (
        randomizer.generate_sequence(
            "prev < current",
            ["ip.ramp_500", "ip.ramp_501", "ip.ramp_502", "ip.ramp_503"],
        )
        == {"ip.ramp_500": 2, "ip.ramp_501": 7, "ip.ramp_502": 18, "ip.ramp_503": 23}
    )


def test_randomizer_generate_sequence_exception(r):
    randomizer = r(seed=12345)
    with pytest.raises(RandomizerError, match="Data generation failed"):
        randomizer.generate_sequence(
            "prev + const2 < current",
            ["ip.ramp_500", "ip.ramp_501"],
            max_tries=5,
            const2=100,
        )


def test_randomizer_generate_conditional(r):
    randomizer = r(seed=12345)
    assert (
        randomizer.generate_conditional(
            "ip.delay_502 >= ip.delay_503 + ip.ramp_503",
        )
        == {"ip.delay_502": 73, "ip.delay_503": 21, "ip.ramp_503": 27}
    )
    assert (
        randomizer.generate_conditional(
            "ip.delay_502 >= ip.delay_503 + ip.ramp_503",
        )
        == {"ip.delay_502": 75, "ip.delay_503": 40, "ip.ramp_503": 12}
    )


def test_randomizer_generate_conditional_exception(r):
    randomizer = r(seed=12345)
    with pytest.raises(RandomizerError, match="Data generation failed"):
        randomizer.generate_conditional(
            "ip.delay_502 >= ip.delay_503 + const2",
            max_tries=10,
            const2=100,
        )
