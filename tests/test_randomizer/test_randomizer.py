#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
from itertools import product
from copy import deepcopy
import pytest
from mimesis import BaseProvider
from roast.providers.randomizer import Randomizer, WeightPreset
from roast.exceptions import RandomizerError
from roast.confParser import generate_conf
from roast.utils import read_json


class Provider1(BaseProvider):
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
    def _r(seed=None, randomize=True):
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
        "data",
        "evaluate",
        "excludes_file",
        "my_provider",
        "parameters",
        "parser",
        "provider2",
        "randomize",
        "replace",
        "rng",
        "shuffle",
        "weights",
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
    for _ in range(10):
        randomizer = r(seed)
        choice_values.append(randomizer.choice(range(1000)))
        choices_values.extend(randomizer.choices(list(range(1000))))
    assert set(choice_values) == {261}
    assert set(choices_values) == {255}


def test_randomizer_seeded_shuffle(r):
    values = []
    seed = 8195374381
    for _ in range(10):
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


@pytest.mark.parametrize(
    "items, weights, length",
    [
        (["a", "b", "c", "d", "e", "f", "g"], [1, 1, 1, 1, 1, 1, 1], 4),
        (["a", "b", "c", "d", "e", "f", "g"], [1, 1, 1, 1, 1, 1, 1], 5),
        (["a", "b", "c", "d", "e", "f", "g"], [1, 1, 1, 1, 1, 1, 1], 1),
        (("a", "b", "c", "d", "e", "f", "g"), [1, 1, 1, 1, 1, 1, 1], 4),
        (("a", "b", "c", "d", "e", "f", "g"), [1, 1, 1, 1, 1, 1, 1], 5),
        (("a", "b", "c", "d", "e", "f", "g"), [1, 1, 1, 1, 1, 1, 1], 1),
        ("abcdefg", [1, 1, 1, 1, 1, 1, 1], 4),
        ("abcdefg", [1, 1, 1, 1, 1, 1, 1], 5),
        ("abcdefg", [1, 1, 1, 1, 1, 1, 1], 1),
    ],
)
def test_choices(r, weights, items, length):
    randomizer = Randomizer()
    result = randomizer.choices(items=items, weights=weights, length=length)
    assert len(result) == length
    assert type(result) is type(items)


@pytest.mark.parametrize(
    "items",
    [
        ["a", "b", "c", "d", "c", "b", "a"],
        ("a", "b", "c", "d", "c", "b", "a"),
        "abcdcba",
    ],
)
def test_choices_unique(r, items):
    randomizer = Randomizer()
    result = randomizer.choices(items=items, length=4, unique=True)
    assert len(result) == len(set(result))
    assert type(result) is type(items)


@pytest.mark.parametrize(
    "items",
    [
        ["a", "b", "c", "d", "e"],
        ("a", "b", "c", "d", "e"),
        "abcde",
    ],
)
def test_choices_one_element(r, items):
    randomizer = Randomizer()
    result = randomizer.choices(items=items)
    assert isinstance(result, type(items))


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


def test_choices_empty_items(r):
    randomizer = r()
    with pytest.raises(ValueError):
        randomizer.choices(items=[])


def test_choices_negative_length(r):
    randomizer = r()
    with pytest.raises(ValueError):
        randomizer.choices(items=("a", "b"), length=-1)


def test_choices_insufficient_unique(r):
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


def test_randomizer_no_randomize(r):
    randomizer = r(seed=12345, randomize=False)
    assert randomizer.get_value("ip.attribute1") == 64
    assert randomizer.get_value("ip.attribute2") == 127
    assert randomizer.get_value("ip.attribute3") == 9
    assert randomizer.get_value("ip.attribute5") == 2
    assert randomizer.get_value("ip.attribute6") == 14
    assert randomizer.get_value("ip.attribute7") == 1.4
    assert randomizer.get_value("ip.attribute8") == -1.4
    assert randomizer.get_value("ip.attribute9") == -1.6
    assert randomizer.get_value("ip.attribute10") == 18


def test_randomizer_no_randomize_param(r):
    randomizer = r(seed=12345)
    assert randomizer.get_value("ip.attribute1") == 256
    assert randomizer.get_value("ip.attribute10") == 18


def test_randomizer_exception(r):
    randomizer = r(seed=12345, randomize=True)
    with pytest.raises(KeyError, match="Attribute ip.attribute0 not defined"):
        randomizer.get_value("ip.attribute0")
    with pytest.raises(KeyError, match="Attribute ip.attribute0 not defined"):
        randomizer.get_all_values("ip.attribute0")
    with pytest.raises(
        KeyError, match="For attribute ip.attribute4, elements or range not defined"
    ):
        randomizer.get_value("ip.attribute4")
    with pytest.raises(
        KeyError, match="For attribute ip.attribute4, elements or range not defined"
    ):
        randomizer.get_all_values("ip.attribute4")

    randomizer = r(randomize=False)
    with pytest.raises(KeyError, match="Default value for ip.attribute11 not defined"):
        randomizer.get_value("ip.attribute11")


def test_randomizer_get_all_values(r):
    randomizer = r()
    assert randomizer.get_all_values("ip.attribute1") == [32, 256, 512]
    attribute2 = list(range(256))
    attribute2.remove(35)
    attribute2.remove(36)
    attribute2.remove(37)
    assert randomizer.get_all_values("ip.attribute2") == attribute2
    assert randomizer.get_all_values("ip.attribute3") == list(range(128))
    attribute5 = [0, 2, 8, 10]
    assert randomizer.get_all_values("ip.attribute5") == attribute5
    assert randomizer.get_all_values("ip.attribute6") == list(range(21))
    attribute7 = [0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0]
    assert randomizer.get_all_values("ip.attribute7") == attribute7
    attribute8 = [0, -0.2, -0.4, -0.6, -0.8, -1.0, -1.2, -1.4, -1.6, -1.8, -2.0]
    assert randomizer.get_all_values("ip.attribute8") == attribute8
    attribute9 = [-2.0, -1.8, -1.6, -1.4, -1.2, -1.0]
    assert randomizer.get_all_values("ip.attribute9") == attribute9
    for _ in range(10):
        randomizer.get_value("ip.ramp_500")
    assert randomizer.get_all_values("ip.ramp_500") == list(range(1, 31))


def test_randomizer_boolean(r):
    boolean_values = []
    for _ in range(10):
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
    assert randomizer.generate_sequence(
        "prev < current",
        ["ip.ramp_500", "ip.ramp_501", "ip.ramp_502", "ip.ramp_503"],
    ) == {"ip.ramp_500": 2, "ip.ramp_501": 7, "ip.ramp_502": 18, "ip.ramp_503": 23}


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
    assert randomizer.generate_conditional(
        "ip.delay_502 >= ip.delay_503 + ip.ramp_503",
    ) == {"ip.delay_502": 73, "ip.delay_503": 21, "ip.ramp_503": 27}
    assert randomizer.generate_conditional(
        "ip.delay_502 >= ip.delay_503 + ip.ramp_503",
    ) == {"ip.delay_502": 75, "ip.delay_503": 40, "ip.ramp_503": 12}


def test_randomizer_generate_conditional_exception(r):
    randomizer = r(seed=12345)
    with pytest.raises(RandomizerError, match="Data generation failed"):
        randomizer.generate_conditional(
            "ip.delay_502 >= ip.delay_503 + const2",
            max_tries=10,
            const2=100,
        )


def test_shuffle(r):
    randomizer = r(seed=123456)
    x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    assert randomizer.shuffle(x) == [8, 4, 2, 10, 7, 6, 9, 3, 1, 5]
    y = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    assert randomizer.shuffle(y) == (6, 3, 9, 7, 5, 1, 10, 8, 4, 2)
    z = "abcdefghij"
    assert randomizer.shuffle(z) == "bhifgedjca"


def test_shuffle_essential(r):
    randomizer = r(seed=123456)
    x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    essential = [3, 6, 9]
    assert randomizer.shuffle(x, essential) == [2, 4, 9, 3, 6, 1, 5]
    assert randomizer.shuffle(x, essential) == [5, 10, 1, 4, 2, 3, 9, 8, 6]
    y = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    assert randomizer.shuffle(y, essential) == (9, 6, 3)
    assert randomizer.shuffle(y, essential) == (9, 6, 7, 3)
    z = "abcdefghij"
    essential = "fjb"
    assert randomizer.shuffle(z, essential) == "agbjif"
    assert randomizer.shuffle(z, essential) == "adfjigbec"


def test_shuffle_essential_fixed_length(r):
    randomizer = r(seed=123456)
    x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    essential = [3, 6, 9]
    assert randomizer.shuffle(x, essential, length=4) == [6, 9, 5, 3]
    assert randomizer.shuffle(x, essential, length=5) == [6, 1, 2, 3, 9]
    y = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    assert randomizer.shuffle(y, essential, length=6) == (6, 1, 8, 3, 9, 7)
    assert randomizer.shuffle(y, essential, length=7) == (3, 2, 6, 10, 1, 8, 9)
    z = "abcdefghij"
    essential = "fjb"
    assert randomizer.shuffle(z, essential, length=8) == "jbehadgf"
    assert randomizer.shuffle(z, essential, length=9) == "defjiabgc"


def test_shuffle_length_no_essential(r):
    randomizer = r(seed=123456)
    x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    assert randomizer.shuffle(x, length=6) == [5, 1, 3, 9, 6, 7]
    y = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    assert randomizer.shuffle(y, length=7) == (1, 5, 10, 8, 2, 4, 6)
    z = "abcdefghij"
    assert randomizer.shuffle(z, length=5) == "aicdf"


def test_shuffle_non_sequence_items(r):
    randomizer = r()
    with pytest.raises(TypeError):
        randomizer.shuffle(items=5)


def test_shuffle_empty_items(r):
    randomizer = r()
    with pytest.raises(ValueError):
        randomizer.shuffle(items=[])


def test_shuffle_essential_in_items(r):
    randomizer = r()
    with pytest.raises(ValueError):
        randomizer.shuffle(items=[1, 2, 3, 4, 5], essential=[1, 6])


def test_shuffle_insufficient(r):
    randomizer = r()
    with pytest.raises(ValueError):
        randomizer.shuffle(items=["a", "b"], length=3)
    with pytest.raises(ValueError):
        randomizer.shuffle(items=[1, 2, 3], essential=[1], length=4)


def test_randomizer_through_config():
    randomizer = Randomizer(seed=123456)
    config = generate_conf()
    randomizer.parameters = config.parameters1
    assert randomizer.get_value("ip.attribute1") == 256
    assert randomizer.get_value("ip.attribute2") == 7
    assert randomizer.get_value("ip.attribute3") == 0.4
    assert randomizer.get_value("ip.attribute4") == 18
    assert randomizer.get_value("ip.attribute5") == 20

    randomizer = Randomizer(seed=123456)
    config = generate_conf()
    randomizer.parameters = config.parameters2
    assert randomizer.get_value("ip.attribute1") == 256
    assert randomizer.get_value("ip.attribute2") == 7
    assert randomizer.get_value("ip.attribute3") == 0.4
    assert randomizer.get_value("ip.attribute4") == 18
    assert randomizer.get_value("ip.attribute5") == 20


def test_randomizer_excludes_file(r, tmpdir):
    randomizer = r(seed=12345)
    randomizer.excludes_file = os.path.join(tmpdir, "random_data.json")
    randomizer.get_value("ip.attribute1")
    randomizer.get_value("ip.attribute2")
    randomizer.get_value("ip.attribute3")
    randomizer.get_value("ip.attribute5")
    randomizer.get_value("ip.attribute6")
    randomizer.get_value("ip.attribute7")
    randomizer.get_value("ip.attribute8")
    randomizer.get_value("ip.attribute9")
    randomizer.to_json()
    assert read_json(randomizer.excludes_file) == {
        "ip": {
            "attribute1": [256],
            "attribute2": [190],
            "attribute3": [2],
            "attribute5": [8],
            "attribute6": [11],
            "attribute7": [0.6],
            "attribute8": [-0.8],
            "attribute9": [-1.2],
        }
    }


def test_randomizer_generate_sequence_file(r, tmpdir):
    randomizer = r(seed=123456)
    randomizer.excludes_file = os.path.join(tmpdir, "random_data.json")
    for _ in range(2):
        data = randomizer.generate_sequence(
            "prev < current",
            ["ip.delay_500", "ip.delay_501", "ip.delay_502", "ip.delay_503"],
        )
        randomizer.to_json()
    assert read_json(randomizer.excludes_file) == {
        "ip": {
            "delay_500": [57, 25],
            "delay_501": [82, 33],
            "delay_502": [87, 84],
            "delay_503": [91, 94],
        }
    }


def test_randomizer_generate_conditional_file(r, tmpdir):
    randomizer = r(seed=12345)
    randomizer.excludes_file = os.path.join(tmpdir, "random_data.json")
    for _ in range(2):
        randomizer.generate_conditional(
            "ip.delay_502 >= ip.delay_503 + ip.ramp_503",
        )
        randomizer.to_json()
    assert read_json(randomizer.excludes_file) == {
        "ip": {"delay_502": [73, 76], "delay_503": [21, 54], "ramp_503": [27, 18]}
    }


def test_randomizer_without_replacement(r, tmpdir):
    # global, self.replace = False
    for _ in range(2):
        randomizer = r(seed=12345)
        randomizer.excludes_file = os.path.join(tmpdir, "random_data.json")
        randomizer.get_value("ip.attribute1")
        randomizer.to_json()
    assert read_json(randomizer.excludes_file) == {"ip": {"attribute1": [256, 512]}}

    # parameter replace override
    randomizer = r(seed=12345)
    for _ in range(2):
        randomizer.get_value("ip.attribute11")
    assert randomizer.data == {"ip.attribute11": [26, 20]}


def test_randomizer_param_without_replacement(r, tmpdir):
    for _ in range(2):
        randomizer = r(seed=12345)
        randomizer.excludes_file = os.path.join(tmpdir, "random_data.json")
        randomizer.get_value("ip.attribute11")
        randomizer.to_json()
    assert read_json(randomizer.excludes_file) == {"ip": {"attribute11": [26, 27]}}


def test_randomizer_reset_excluded_attribute(r, tmpdir):
    randomizer = r()
    randomizer.excludes_file = os.path.join(tmpdir, "random_data.json")
    for _ in range(3):
        randomizer.get_value("ip.attribute1")
    assert sorted(randomizer.data["ip.attribute1"]) == [32, 256, 512]
    assert randomizer.get_all_values("ip.attribute1") == []
    for _ in range(4):
        randomizer.get_value("ip.attribute5")
    assert sorted(randomizer.data["ip.attribute5"]) == [0, 2, 8, 10]
    assert randomizer.get_all_values("ip.attribute5") == []
    randomizer.to_json()

    randomizer = r()
    randomizer.excludes_file = os.path.join(tmpdir, "random_data.json")
    assert sorted(randomizer.data["ip.attribute1"]) == [32, 256, 512]
    assert randomizer.get_all_values("ip.attribute1") == []

    values = []
    for _ in range(15):
        try:
            value = randomizer.get_value("ip.attribute1")
            values.append(value)
        except ValueError:
            randomizer.reset_excluded("ip.attribute1")
    assert len(values) == 11
    assert sorted(read_json(randomizer.excludes_file)["ip"]["attribute1"]) == []
    assert sorted(read_json(randomizer.excludes_file)["ip"]["attribute5"]) == [
        0,
        2,
        8,
        10,
    ]


def test_randomizer_reset_excluded_file(r, tmpdir):
    randomizer = r()
    randomizer.excludes_file = os.path.join(tmpdir, "random_data.json")
    for _ in range(3):
        randomizer.get_value("ip.attribute1")
    assert sorted(randomizer.data["ip.attribute1"]) == [32, 256, 512]
    assert randomizer.get_all_values("ip.attribute1") == []
    for _ in range(4):
        randomizer.get_value("ip.attribute5")
    assert sorted(randomizer.data["ip.attribute5"]) == [0, 2, 8, 10]
    assert randomizer.get_all_values("ip.attribute5") == []
    randomizer.to_json()

    randomizer = r()
    randomizer.excludes_file = os.path.join(tmpdir, "random_data.json")
    assert sorted(randomizer.data["ip.attribute5"]) == [0, 2, 8, 10]
    assert randomizer.get_all_values("ip.attribute5") == []

    try:
        randomizer.get_value("ip.attribute1")
    except:
        randomizer.reset_excluded()
    assert read_json(randomizer.excludes_file) == {}


def test_randomizer_formatter(r, tmpdir):
    randomizer = r(seed=12345)
    randomizer.excludes_file = os.path.join(tmpdir, "random_data.json")
    assert randomizer.get_all_values("ip.attribute12") == [
        "0b00000010",
        "0b00001000",
        "0b00010000",
    ]
    assert randomizer.get_all_values("ip.attribute13") == [
        "0x00",
        "0x02",
        "0x04",
        "0x06",
        "0x08",
        "0x0a",
        "0x0c",
        "0x0e",
        "0x10",
    ]
    assert randomizer.get_all_values("ip.attribute14") == [
        "8.000000e+02",
        "8.500000e+02",
        "9.000000e+02",
        "9.500000e+02",
        "1.000000e+03",
        "1.050000e+03",
        "1.100000e+03",
        "1.150000e+03",
        "1.200000e+03",
    ]
    assert randomizer.get_value("ip.attribute12") == "0b00001000"
    assert randomizer.data["ip.attribute12"] == ["0b00001000"]
    randomizer.parameters["ip.attribute12"].randomize = False
    assert randomizer.get_value("ip.attribute12") == "0b00001000"
    assert randomizer.get_value("ip.attribute13") == "0x00"
    assert randomizer.get_value("ip.attribute14") == "1.000000e+03"
    randomizer.to_json()

    randomizer = r(seed=12345)
    randomizer.excludes_file = os.path.join(tmpdir, "random_data.json")
    assert randomizer.get_all_values("ip.attribute12") == ["0b00000010", "0b00010000"]
    assert randomizer.get_all_values("ip.attribute13") == [
        "0x02",
        "0x04",
        "0x06",
        "0x08",
        "0x0a",
        "0x0c",
        "0x0e",
        "0x10",
    ]
    assert randomizer.get_all_values("ip.attribute14") == [
        "8.000000e+02",
        "8.500000e+02",
        "9.000000e+02",
        "9.500000e+02",
        "1.050000e+03",
        "1.100000e+03",
        "1.150000e+03",
        "1.200000e+03",
    ]


def test_randomizer_get_value_distribution(r):
    # range 20 to 30
    randomizer = r(seed=1234567)
    values = []
    for _ in range(10):
        value = randomizer.get_value("ip.ramp_500", preset=WeightPreset.LOW_HEAVY)
        values.append(value)
    assert values == [10, 1, 3, 1, 10, 4, 1, 3, 4, 5]
    randomizer = r(seed=1234567)
    values = []
    for _ in range(10):
        value = randomizer.get_value("ip.ramp_500", preset=WeightPreset.HIGH_HEAVY)
        values.append(value)
    assert values == [30, 26, 29, 26, 30, 29, 23, 28, 29, 30]
    randomizer = r(seed=1234567)
    values = []
    for _ in range(10):
        value = randomizer.get_value("ip.ramp_500", preset=WeightPreset.NORMAL)
        values.append(value)
    assert values == [24, 12, 17, 12, 24, 17, 8, 16, 17, 20]
    randomizer = r(seed=1234567)
    values = []
    for _ in range(10):
        value = randomizer.get_value("ip.ramp_500", preset=WeightPreset.INVERSE_NORMAL)
        values.append(value)
    assert values == [30, 5, 19, 5, 30, 21, 1, 17, 20, 27]
    randomizer = r(seed=1234567)
    values = []
    for _ in range(10):
        value = randomizer.get_value("ip.ramp_500", preset=WeightPreset.EXTREME_LIMITS)
        values.append(value)
    assert values == [30, 1, 26, 1, 30, 28, 1, 21, 28, 30]

    # range 1 to 100 with replace = False
    randomizer = r(seed=1234567)
    values = []
    for _ in range(10):
        value = randomizer.get_value("ip.attribute15", preset=WeightPreset.LOW_HEAVY)
        values.append(value)
    assert values == [31, 3, 10, 4, 33, 12, 1, 11, 13, 19]
    assert len(randomizer.weights["ip.attribute15"]) == 90
    # range 1 to 100 with replace = False, LOW_HEAVY preset from config
    randomizer = r(seed=1234567)
    values = []
    for _ in range(10):
        value = randomizer.get_value("ip.attribute16")
        values.append(value)
    assert values == [31, 3, 10, 4, 33, 12, 1, 11, 13, 19]
    # range 1 to 100 with replace = False, shape (a=1, b=10) from config
    randomizer = r(seed=1234567)
    values = []
    for _ in range(10):
        value = randomizer.get_value("ip.attribute17")
        values.append(value)
    assert values == [31, 3, 10, 4, 33, 12, 1, 11, 13, 19]
    # range 1 to 100 with replace = False, preset override
    randomizer = r(seed=1234567)
    values = []
    for _ in range(10):
        value = randomizer.get_value("ip.attribute17", preset=WeightPreset.HIGH_HEAVY)
        values.append(value)
    assert values == [100, 86, 94, 84, 99, 93, 73, 92, 95, 97]

    randomizer = r(seed=1234567)
    values = []
    for _ in range(10):
        value = randomizer.get_value("ip.ramp_500", b=10)  # LOW_HEAVY, a=1
        values.append(value)
    assert values == [10, 1, 3, 1, 10, 4, 1, 3, 4, 5]


def test_generate_weights_exception(r):
    length = 0xFFFFFFFF
    randomizer = r()
    with pytest.raises(MemoryError, match="Unable to allocate"):
        randomizer.generate_weights(length)
