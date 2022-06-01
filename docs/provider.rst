===============
 Data Provider
===============

The ROAST data provider (randomization engine) is a data generator based on the `Mimesis`_ open
source library.

The generated data can be used to define a range of values or a set of discrete values for a
parameter of a component. Examples include:

- Clock divider where the value can be from 3 to 7
- Bus data width where the value can be 32, 64, or 128 bits
  
The functions supplied by this engine are bound to the Python `random`_ module. While the examples
shown are numerical based, the base functions can use objects for elements within sequences. For
example, the order of objects within a sequence can be randomized when calling the shuffle method.

Randomizer class
================

The ``Randomizer`` class is the base provider. The functionality includes:

.. contents::
   :local:

Initialize random generator with seed
-------------------------------------

An optional seed can be provided for reproducable randomization. If seed is omitted or ``None``,
the current system time is used.

.. code-block:: python

    >>> from roast.providers.randomizer import Randomizer
    >>> randomizer = Randomizer(seed=12345)

Disable randomization
---------------------

In some scenarios, randomization may need to be disabled. Randomization is enabled by default and
can be disabled at the global or parameter level. To disable, set ``randomize`` to ``False``. When
disabled, the ``default`` value will be returned.

.. code-block:: python

    >>> from roast.providers.randomizer import Randomizer
    >>> randomizer = Randomizer(randomize=False)

To disable at the parameter level, set the ``randomize`` property to ``False`` when loading
parameter values into the data provider. Both ``default`` and ``randomize`` properties are
discussed in the section, `Load provider with JSON data file`_.

Random module
-------------

The `random`_ module can be accessed directly through the class for methods such as the
distribution functions.

.. code-block:: python

    >>> from roast.providers.randomizer import Randomizer
    >>> randomizer = Randomizer()
    >>> randomizer.random.random()
    0.27405095889396036
    >>> randomizer.random.uniform(10, 100)
    23.291595105628538

.. _json-data:

Load provider with JSON data file
---------------------------------

A JSON data file can be loaded to establish a database of parameters and possible values.

.. code-block:: json
   :caption: parameters.json

    {
        "ip": {
            "attribute1": {
                "default": 64,
                "elements": [32, 64, 128, 256, 512],
                "excluded": [64, 128]
            },
            "attribute2": {
                "default": 127,
                "range": [0, 255],
                "excluded": [35, 36, 37]
            },
            "attribute3": {
                "default": 1.4,
                "range": [0, 2, 0.2]
            },
            "attribute4": {
                "default": 18,
                "range": [10, 20],
                "randomize": false
            },
            "attribute5": {
                "range": [20, 30],
                "replace": false
            },
            "attribute6": {
                "default": "0X08",
                "elements": ["0x02", "0o10", "0b10000"],
                "format": "#010b"
            },
            "attribute7": {
                "default": "0x0C",
                "range": ["0X00", "0O20", "0B10"],
                "format": "#04x"
            },
            "attribute8": {
                "default": "1.000000e+03",
                "range": ["8.000000e+02", "1.200000e+03", 50],
                "format": "e"
            },
            "attribute9": {
                "range": [1, 100]
            },
            "attribute10": {
                "range": [1, 100],
                "preset": "LOW_HEAVY"
            },
            "attribute11": {
                "range": [1, 100],
                "shape": [1, 10]
            }
        }
    }

For each attribute, there are nine properties that can be defined:

#. **elements** - Sequence of discrete values.
#. **range** - Sequence of range parameters: start, stop, and step.

    - If one value is provided, it is the stop value. It assumes that start is 0 and step is 1.
    - If two values are provided, it is the start and stop values. It assumes step is 1.
#. **excluded** - Sequence of values to never return.
#. **default** - Value returned if the global ``randomize`` or parameter ``randomize`` is set to ``False``.
#. **format** - Defines how string values are presented. See `Format Specification Mini-Language`_ for details. To specify hex, octal, or binary formatted strings, use the alternative format starting with ``#``.
#. **randomize** -  Boolean to disable randomization for the specific parameter.
#. **replace** - Boolean to determine whether sampling is with or without replacement. This setting will override the global ``replace`` setting.
#. **preset** - Weighted randomization preset to use to shape the generated data. ``LOW_HEAVY``, ``HIGH_HEAVY``, ``NORMAL``, ``INVERSE_NORMAL``, and ``EXTERME_LIMITS``.
#. **shape** - Sequence of shape parameter values for the randomization distribution function. This is for the Alpha and Beta values of the Beta distribution.

.. note::

    - See :ref:`exclude-values` for details on usage of ``replace``.
    - See :ref:`weighted-distribution` for details on usage of ``preset`` and ``shape``.

.. warning::

    - Either ``elements`` or ``range`` must exist or an exception will be raised. Both should not be used in the same attribute. If both exist, ``elements`` will have priority.
    - Both ``preset`` and ``shape`` should not be used for the same attribute. If both exist, ``preset`` will have priority.

When a JSON file is specified, it is read and stored into ``parameters``.

.. code-block:: python

    >>> from roast.providers.randomizer import Randomizer
    >>> randomizer = Randomizer()
    >>> randomizer.datafile = "parameters.json"
    >>> randomizer.parameters
    <Box: {'ip': {'attribute1': {'default': 64, 'elements': [32, 64, 128, 256, 512], 'excluded': [64, 128]}, 'attribute2': {'default': 127, 'range': [0, 255], 'excluded': [35, 36, 37]}, 'attribute3': {'default': 9, 'range': [0, 127]}, 'attribute4': {'default': 127}, 'attribute5': {'default': 2, 'range': [0, 10, 2], 'excluded': [4, 6]}, 'attribute6': {'default': 14, 'range': [20]}, 'attribute7': {'default': 1.4, 'range': [0, 2, 0.2]}, 'attribute8': {'default': -1.4, 'range': [0, -2, -0.2]}, 'attribute9': {'default': -1.6, 'range': [-2, -1, 0.2]}, 'attribute10': {'default': 18, 'range': [10, 20], 'randomize': False}, 'attribute11': {'range': [20, 30], 'replacement': False}, 'attribute12': {'default': 8, 'elements': [2, 8, 16], 'format': '#010b'}, 'attribute13': {'default': 12, 'range': [0, 16, 2], 'format': '#04x'}, 'attribute14': {'default': 1000.0, 'range': [800.0, 1200.0, 50], 'format': 'e'}, 'delay_500': {'default': 52, 'range': [20, 100]}, 'delay_501': {'default': 52, 'range': [20, 100]}, 'delay_502': {'default': 52, 'range': [20, 100]}, 'delay_503': {'default': 52, 'range': [20, 100]}, 'ramp_500': {'default': 2, 'range': [1, 30]}, 'ramp_501': {'default': 2, 'range': [1, 30]}, 'ramp_502': {'default': 2, 'range': [1, 30]}, 'ramp_503': {'default': 2, 'range': [1, 30]}}}>

To retrieve the default value of ``ip.attribute1``:

.. code-block:: python

    >>> from roast.providers.randomizer import Randomizer
    >>> randomizer = Randomizer(randomize=False)
    >>> randomizer.datafile = "parameters.json"
    >>> randomizer.get_value("ip.attribute1")
    64
    >>> randomizer.get_value("ip.attribute6")
    '0b00001000'
    >>> randomizer.get_value("ip.attribute7")
    '0x0c'
    >>> randomizer.get_value("ip.attribute8")
    '1.000000e+03'

.. note::

    - Internally, string values are converted to ``float``. Hex, octal, and binary strings are converted to ``int``.
    - Changed in version 4.0: ``values`` replaced with ``elements`` due to library conflict.
    - Added in versions 4.0: ``format``, ``randomize``, ``replace``, ``preset``, and ``shape`` properties.

Load provider through configuration
-----------------------------------

The randomization parameters can be loaded through configuration. The same properties defined
in the previous section, :ref:`json-data`, are used. To load through configuration, the parameters
will need to be defined within a `Box`_ so that dot-based keys can be used to traverse the
dictionary. After the configuration is generated, store it into ``parameters``. There are two
methods to define through configuration.

**Method 1 (nested dictionary)**:

.. code-block:: python
    :caption: conf.py

    from box import Box

    parameters = Box(
        {
            "ip": {
                "attribute1": {
                    "default": 64,
                    "elements": [32, 64, 128, 256, 512],
                    "excluded": [64, 128]
                },
                "attribute2": {
                    "default": 127,
                    "range": [0, 255],
                    "excluded": [35, 36, 37]
                },
                "attribute3": {
                    "default": 1.4,
                    "range": [0, 2, 0.2]
                },
                "attribute4": {
                    "default": 18,
                    "range": [10, 20],
                    "randomize": false
                },
                "attribute5": {
                    "range": [20, 30],
                    "replace": false
                }
            }
        },
        box_dots=True,
    )

    del Box

**Method 2 (dot-based)**:

.. code-block:: python
    :caption: conf.py

    from box import Box

    parameters = Box(default_box=True, box_intact_types=[list, tuple])
    parameters.ip.attribute1.default = 64
    parameters.ip.attribute1.elements = [32, 64, 128, 256, 512]
    parameters.ip.attribute1.excluded = [64, 128]
    parameters.ip.attribute2.default = 127
    parameters.ip.attribute2.range = [0, 255]
    parameters.ip.attribute2.excluded = [35, 36, 37]
    parameters.ip.attribute3.default = 1.4
    parameters.ip.attribute3.range = [0, 2, 0.2]
    parameters.ip.attribute4.default = 18
    parameters.ip.attribute4.range = [10, 20]
    parameters.ip.attribute4.randomize = False
    parameters.ip.attribute5.range = [20, 30]
    parameters.ip.attribute5.replace = False

    del Box

With either method, the configuration can be generated through the :doc:`configuration`. If using
``pytest``, use the fixture for :ref:`pytest_fixtures:Configuration Generation`. 

.. code-block:: bash

    >>> from roast.providers.randomizer import Randomizer
    >>> from roast.confParser import generate_conf
    >>> randomizer = Randomizer()
    >>> config = generate_conf()
    >>> randomizer.parameters = config.parameters
    >>> randomizer.get_value("ip.attribute1")
    256
    
.. note::

    New in version 4.0.

Boolean choice
--------------

This will randomly return ``True`` or ``False``.

.. code-block:: python

    >>> from roast.providers.randomizer import Randomizer
    >>> randomizer = Randomizer()
    >>> randomizer.boolean()
    False
    >>> randomizer.boolean()
    True

All possible values
-------------------

The does not have any randomization and is a helper function to return all possible values with excluded values removed.

.. code-block:: python

    >>> from roast.providers.randomizer import Randomizer
    >>> randomizer = Randomizer()
    >>> randomizer.datafile = "parameters.json"
    >>> randomizer.get_all_values("ip.attribute1")
    [32, 256, 512]
    >>> randomizer.get_all_values("ip.attribute8")
    ['8.000000e+02', '8.500000e+02', '9.000000e+02', '9.500000e+02', '1.000000e+03', '1.050000e+03', '1.100000e+03', '1.150000e+03', '1.200000e+03']

Single random value
-------------------

This will return a random element.

.. code-block:: python

    >>> from roast.providers.randomizer import Randomizer
    >>> randomizer = Randomizer()
    >>> randomizer.datafile = "parameters.json"
    >>> randomizer.get_value("ip.attribute1")
    256
    >>> randomizer.get_value("ip.attribute7")
    '0x10'

.. _weighted:

Sequence of random values (weighted)
------------------------------------

A sequence of choices can be randomly generated from a sequence of values. There are three options:

#. Length - To define how many elements are in returned sequence.
#. Weights - To define which elements should be selected more often. The weights can be relative.
#. Unique - To define if any selected elements can be repeated.

.. code-block:: python

    >>> from roast.providers.randomizer import Randomizer
    >>> randomizer = Randomizer()
    >>> randomizer.datafile = "parameters.json"
    >>> attribute3 = randomizer.get_all_values("ip.attribute3")
    >>> attribute3
    [0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0]
    >>> randomizer.choices(attribute3, length=4)
    [0.4, 1.0, 1.0, 1.2]
    >>> randomizer.choices(attribute3, length=4, unique=True)
    [0.6, 0, 0.8, 1.8]
    >>> weights = [10, 1, 1, 1, 10, 10, 1, 1, 1, 1, 10]
    >>> randomizer.choices(attribute3, weights, length=4)
    [0.4, 0, 1.0, 1.0]
    >>> randomizer.choices(attribute3, weights, length=4, unique=True)
    [2.0, 1.0, 0.8, 0]

Sequence of random values (essential)
-------------------------------------

A sequence of choices randomly generated from a sequence of values defined with essential elements.
This can also be considered as a constrained shuffle. This is similar to the previous type,
:ref:`weighted`, without weights and results are always unique. There are two options:

#. Essential - To define which elements must be included in returned sequence.
#. Length - To define how many elements are in returned sequence.

Behaviors:

- By default, if both ``essential`` and ``length`` are not specified, a normal shuffle will be returned.
- If only ``essential`` is specified, a random length between the length of ``essential`` sequence and
  the length of ``items`` will be returned.

.. code-block:: python

    >>> from roast.providers.randomizer import Randomizer
    >>> randomizer = Randomizer()
    >>> randomizer.shuffle(items=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    [8, 4, 2, 10, 7, 6, 9, 3, 1, 5]
    >>> randomizer.shuffle(items=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10), length=7)
    (1, 5, 10, 8, 2, 4, 6)
    >>> randomizer.shuffle(items=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], essential=[3, 6, 9])
    [2, 9, 5, 7, 3, 6, 8]
    >>> randomizer.shuffle(items=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10), essential=[3, 6, 9], length=5)
    (5, 6, 7, 3, 9)

.. note::

    New in version 4.0.

.. _weighted-distribution:

Single or sequence of random values (weighted distribution)
-----------------------------------------------------------

A single or sequence of choices can be randomly generated from a sequence of values based on the
Beta probability distribution. Presets are available to provide predetermined probability of an
element being selected from the provided sequence of elements.

- LOW_HEAVY - elements near lower end more frequently
- HIGH_HEAVY - elements near higher end more frequently
- NORMAL - elements near median more frequently
- INVERSE_NORMAL - elements near ends more frequently
- EXTREME_LIMITS - elements near ends significantly more frequently
  
.. code-block:: json
   :caption: parameters.json

    {
        "ip": {
            "attribute9": {
                "range": [1, 100]
            },
            "attribute10": {
                "range": [1, 100],
                "preset": "LOW_HEAVY"
            },
            "attribute11": {
                "range": [1, 100],
                "shape": [1, 10]
            }
        }
    }

.. code-block:: python

    >>> from roast.providers.randomizer import Randomizer
    >>> randomizer = Randomizer()
    >>> randomizer.datafile = "parameters.json"
    >>> values = []
    >>> for _ in range(10):
    ...     value = randomizer.get_value("ip.attribute10") # LOW_HEAVY
    ...     values.append(value)
    ... 
    >>> values
    [1, 13, 7, 17, 38, 21, 21, 16, 7, 7]
    >>>
    >>> randomizer = Randomizer()
    >>> randomizer.datafile = "parameters.json"
    >>> values = []
    >>> for _ in range(10):
    ...     value = randomizer.get_value("ip.attribute11") # a=1, b=10
    ...     values.append(value)
    ... 
    >>> values
    [1, 2, 3, 9, 3, 8, 3, 2, 13, 22]

The preset can be directly specified when calling ``get_value()``. This will override any setting
specified in the configuration.

.. code-block:: python

    >>> from roast.providers.randomizer import Randomizer, WeightPreset
    >>> randomizer = Randomizer()
    >>> randomizer.datafile = "parameters.json"
    >>> values = []
    >>> for _ in range(10):
    ...     value = randomizer.get_value("ip.attribute9", preset=WeightPreset.LOW_HEAVY)
    ...     values.append(value)
    ... 
    >>> values
    [5, 3, 9, 35, 12, 5, 5, 9, 18, 15]
    >>>
    >>> randomizer = Randomizer()
    >>> randomizer.datafile = "parameters.json"
    >>> values = []
    >>> for _ in range(10):
    ...     value = randomizer.get_value("ip.attribute9", preset=WeightPreset.HIGH_HEAVY)
    ...     values.append(value)
    ... 
    >>> values
    [94, 95, 90, 99, 97, 93, 90, 80, 99, 97]

The Alpha and Beta shape parameters can also be provided as parameters. As an example, we can
provide the values of the LOW_HEAVY preset. This will also override any setting in the
configuration.

.. code-block:: python

    >>> from roast.providers.randomizer import Randomizer
    >>> randomizer = Randomizer()
    >>> randomizer.datafile = "parameters.json"
    >>> values = []
    >>> for _ in range(10):
    ...     value = randomizer.get_value("ip.attribute9", a=1, b=10)
    ...     values.append(value)
    ... 
    >>> values
    [6, 25, 8, 16, 6, 1, 12, 5, 8, 10]

.. warning::

    When using the weighted distribution feature, the distribution parameters cannot be changed
    on-the-fly. This means that if values have been generated for an attribute using ``LOW_HEAVY``,
    it cannot be changed to generate ``HIGH_HEAVY`` values by simply specifying the new preset.
    This is because the weights for each possible value are generated during the initial call to
    ``get_value()`` and stored in the ``weights`` property within the randomizer for performance
    reasons. If changing of the distribution parameters is needed, instantiate another instance
    of the randomizer or empty the weight array.

Choices defined by expression
-----------------------------

This will return randomized values defined by an expression.

For example, randomized delays and ramp times with a condition to define the relationship.

The condition is ``ip.delay_502 >= ip.delay_503 + ip.ramp_503``

.. code-block:: json
   :caption: parameters.json

    {
        "ip": {
            "delay_502": {
                "default": 52,
                "range": [20, 100]
            },
            "delay_503": {
                "default": 52,
                "range": [20, 100]
            },
            "ramp_503": {
                "default": 2,
                "range": [1, 30]
            }
        }
    }

.. code-block:: python

    >>> from roast.providers.randomizer import Randomizer
    >>> randomizer = Randomizer()
    >>> randomizer.datafile = "parameters.json"
    >>> randomizer.generate_conditional("ip.delay_502 >= ip.delay_503 + ip.ramp_503")
    {'ip.delay_502': 67, 'ip.delay_503': 43, 'ip.ramp_503': 12}

In addition to defined attributes, variables can also be used to be evaluated.

For example, a dynamically defined offset as part of the expression.

The condition is ``ip.delay_502 >= ip.delay_503 + offset``.

.. code-block:: python

    >>> from roast.providers.randomizer import Randomizer
    >>> randomizer = Randomizer()
    >>> randomizer.datafile = "parameters.json"
    >>> offset = 10
    >>> randomizer.generate_conditional("ip.delay_502 >= ip.delay_503 + offset", offset=offset)
    {'ip.delay_502': 80, 'ip.delay_503': 40}
    >>> offset = 20
    >>> randomizer.generate_conditional("ip.delay_502 >= ip.delay_503 + offset", offset=offset)
    {'ip.delay_502': 100, 'ip.delay_503': 65}

The complete set of operators that can be used are listed in the `Arithmetic Parser User Guide`_.

Sequence of choices defined by expression
-----------------------------------------

This will return a sequence of randomized values based on a condition.

For example, a randomized sequence of four delay values where the each random value needs to be
greater than the previous where the condition is: ``delay_500 < delay_501 < delay_502 < delay_503``.

.. code-block:: json
   :caption: parameters.json

    {
        "ip": {
            "delay_500": {
                "default": 52,
                "range": [20, 100]
            },
            "delay_501": {
                "default": 52,
                "range": [20, 100]
            },
            "delay_502": {
                "default": 52,
                "range": [20, 100]
            },
            "delay_503": {
                "default": 52,
                "range": [20, 100]
            }
        }
    }

.. code-block:: python

    >>> from roast.providers.randomizer import Randomizer
    >>> randomizer = Randomizer()
    >>> randomizer.datafile = "parameters.json"
    >>> randomizer.generate_sequence("prev < current", ["ip.delay_500", "ip.delay_501", "ip.delay_502", "ip.delay_503"])
    {'ip.delay_500': 41, 'ip.delay_501': 78, 'ip.delay_502': 81, 'ip.delay_503': 86}

While both ``prev`` and ``current`` are pre-defined and can be used to define the condition, any expression can be used.

Within the expression, variables can also be used to be evaluated.

For example, a dynamically defined offset as part of the expression where the condition is ``prev + offset <= current``.

.. code-block:: python

    >>> from roast.providers.randomizer import Randomizer
    >>> randomizer = Randomizer()
    >>> randomizer.datafile = "parameters.json"
    >>> offset = 10
    >>> randomizer.generate_sequence("prev + offset <= current", ["ip.delay_500", "ip.delay_501", "ip.delay_502"], offset=offset)
    {'ip.delay_500': 26, 'ip.delay_501': 36, 'ip.delay_502': 72}

The complete set of operators that can be used are listed in the `Arithmetic Parser User Guide`_.

Exporting generated values
--------------------------

Whenever a random value is generated by the provider, the value is stored into the ``data``
class attribute, a `Box`_ dictionary. This can very useful for debugging purposes and can be
exported to a JSON file. This JSON file can then be used as a database of previously generated
values discussed in the section :ref:`exclude-values`.

Since the dictionary may have dotted keys, a special method is provided to convert any
dotted keys into a nested dictionary that can be properly exported to JSON.

.. code-block:: python

    >>> from roast.providers.randomizer import Randomizer
    >>> randomizer = Randomizer()
    >>> randomizer.datafile = "parameters.json"
    >>> randomizer.get_value("ip.attribute1")
    32
    >>> randomizer.data
    <Box: {'ip.attribute1': [32]}>
    >>> randomizer.to_json("generated.json")
    >>> with open("generated.json", "r") as f:
    ...    parsed = json.load(f)
    ...
    >>> parsed
    {'ip': {'attribute1': [32]}}

.. note::

    New in version 4.0.

.. _exclude-values:

Exclude values used in previous runs
------------------------------------

Values generated by the provider can be excluded for use in subsequent runs. This allows tests to
sample without replacement over multiple runs. To enable this, import the exported data file as
described in the previous section. Upon import, the global ``replace`` property will be
set to ``False``. To override and disable for a parameter, set the ``replace`` property to ``True``
at the parameter level as described in :ref:`json-data`.

By default, samples are with replacement.

.. code-block:: python

    >>> from roast.providers.randomizer import Randomizer
    >>> randomizer = Randomizer(seed=12345)
    >>> randomizer.datafile = "parameters.json"
    >>> randomizer.get_all_values("ip.attribute1")
    [32, 256, 512]
    >>> randomizer.get_value("ip.attribute1")
    512
    >>> randomizer.get_all_values("ip.attribute1")
    [32, 256, 512]

This can be set to without replacement at the parameter level. Example shown is for JSON parameter file.

.. code-block:: json
   :caption: parameters.json

    {
        "ip": {
            "attribute5": {
                "range": [20, 30],
                "replace": false
            }
        }
    }

The value generated from the first call will be excluded from possible values on the next call.

.. code-block:: python

    >>> from roast.providers.randomizer import Randomizer
    >>> randomizer = Randomizer(seed=12345)
    >>> randomizer.datafile = "parameters.json"
    >>> randomizer.get_all_values("ip.attribute5")
    [20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]
    >>> randomizer.get_value("ip.attribute5")
    26
    >>> randomizer.get_all_values("ip.attribute5")
    [20, 21, 22, 23, 24, 25, 27, 28, 29, 30]

To exclude values from an exported data file, load as a excludes file which will set the global
``replace`` property to ``False``. The contents of the excludes file will then be the
initial value of the ``data`` class attribute. After randomized values are generated, optionally
export all of the accumulated values back to the generated values JSON file.

.. code-block:: python

    >>> from roast.providers.randomizer import Randomizer
    >>> randomizer = Randomizer()
    >>> randomizer.datafile = "parameters.json"
    >>> randomizer.get_value("ip.attribute1")
    32
    >>> randomizer.data
    <Box: {'ip.attribute1': [32]}>
    >>> randomizer.to_json("generated.json")
    >>> 
    >>> randomizer = Randomizer()
    >>> randomizer.datafile = "parameters.json"
    >>> randomizer.excludes_file = "generated.json"
    >>> randomizer.data
    <Box: {'ip': {'attribute1': [32]}}>
    >>> randomizer.get_all_values("ip.attribute1")
    [256, 512]
    >>> randomizer.get_value("ip.attribute1")
    512
    >>> randomizer.data
    <Box: {'ip': {'attribute1': [32, 512]}}>
    >>> randomizer.get_all_values("ip.attribute1")
    [256]
    >>> randomizer.to_json()
    >>> with open("generated.json", "r") as f:
    ...    parsed = json.load(f)
    ...
    >>> parsed
    {'ip': {'attribute1': [32, 512]}}

.. warning::

    The parameter setting will override the global setting. For example, if the global setting is
    ``False`` and the parameter setting is ``True``, the attribute will sample with replacement,
    meaning that it will not exclude previously generated values loaded from file.

.. note::

    New in version 4.0.

Custom data providers
---------------------

Custom providers can be created and dynamically added to generate specific data.

.. code-block:: python

    from mimesis import BaseProvider

    class SomeProvider(BaseProvider):
        class Meta:
            name = "some_provider"

        @staticmethod
        def hello():
            return "Hello!"

This can be used as such:

.. code-block:: python

    >>> from roast.providers.randomizer import Randomizer
    >>> randomizer = Randomizer()
    >>> randomizer.add_provider(SomeProvider)
    >>> randomizer.some_provider.hello()
    'Hello!'

Documentation for `Custom Providers`_ at Mimesis website.

.. _random: https://docs.python.org/3/library/random.html
.. _Mimesis: https://https://mimesis.name/
.. _Custom Providers: https://mimesis.name/getting_started.html#custom-providers
.. _Arithmetic Parser User Guide: https://github.com/pyparsing/plusminus/blob/master/doc/arithmetic_parser_user_guide.md
.. _Box: https://github.com/cdgriffith/Box
.. _Format Specification Mini-Language: https://docs.python.org/3/library/string.html#format-specification-mini-language
