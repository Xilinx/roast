===============
 Data Provider
===============

The ROAST data provider (randomization engine) is a data generator based on the `Mimesis`_ open
source library.

The generated data can be used to define a range of values or a set of discrete values for a
parameter of a component. Examples include:

- Clock divider where the value can be from 3 to 7
- Bus data width where the value can be 32, 64, or 128 bits

Randomizer class
================

The ``Randomizer`` class is the base provider. The functionality includes:

.. contents::
   :local:


Initialize random generator with seed
-------------------------------------

An optional seed can be provided for reproducable random sequences. If seed is omitted or `None`,
the current system time is used.

.. code-block:: python

    >>> from roast.providers.randomizer import Randomizer
    >>> randomizer = Randomizer(seed=12345)

Disable randomization
---------------------

In some scenarios, randomization may need to be disabled. When disabled, the ``default``
value will be returned. This is discussed in the next section, `Load provider with JSON data file`_.

By default, randomization is enabled and the ``randomize`` parameter is set to ``True``.
To disable, set ``randomize`` to ``False``.

.. code-block:: python

    >>> from roast.providers.randomizer import Randomizer
    >>> randomizer = Randomizer(randomize=False)

Load provider with JSON data file
---------------------------------

A JSON data file can be loaded to establish a database of parameters and possible values.

.. code-block:: json
   :caption: parameters.json

    {
        "ip": {
            "attribute1": {
                "default": 64,
                "values": [32, 64, 128, 256, 512],
                "excluded" : [64, 128]
            },
            "attribute2": {
                "default": 127,
                "range": [0, 255],
                "excluded" : [35, 36, 37]
            },
            "attribute3": {
                "default": 1.4,
                "range": [0, 2, 0.2]
            }
        }
    }

For each attribute defined, there are four properties:

#. default - This is optional where the default value is returned if ``randomize`` is set to ``False``.
#. values - This is a sequence of discrete values.
#. range - This is a sequence of range parameters: start, stop, and step.

    - If one value is provided, it is the stop value. It assumes that start is 0 and step is 1.
    - If two values are provided, it is the start and stop values. It assumes step is 1.
#. excluded - This is a sequence of values to never return.

To retrieve the default value of ``ip.attribute1``:

.. code-block:: python

    >>> from roast.providers.randomizer import Randomizer
    >>> randomizer = Randomizer(randomize=False)
    >>> randomizer.datafile = "parameters.json"
    >>> randomizer.get_value("ip.attribute1")
    64

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

Return all possible values
--------------------------

The does not have any randomization and is a helper function to return all possible values.

.. code-block:: python

    >>> from roast.providers.randomizer import Randomizer
    >>> randomizer = Randomizer()
    >>> randomizer.datafile = "parameters.json"
    >>> randomizer.get_all_values("ip.attribute1")
    [32, 256, 512]


Get random value
----------------

This will return a random element.

.. code-block:: python

    >>> from roast.providers.randomizer import Randomizer
    >>> randomizer = Randomizer()
    >>> randomizer.datafile = "parameters.json"
    >>> randomizer.get_value("ip.attribute1")
    256

Get a sequence of random values
-------------------------------

A sequence of choices can be randomly generated from a sequence of values. There are three options:

#. Length - To define how many elements are in returned sequence
#. Weights - To defiine which elements should be selected more often. The weights can be relative.
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
    offset = 10
    >>> randomizer.generate_conditional("ip.delay_502 >= ip.delay_503", offset=offset)
    {'ip.delay_502': 80, 'ip.delay_503': 40}
    >>> offset = 20
    >>> randomizer.generate_conditional("ip.delay_502 >= ip.delay_503", offset=offset)
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


.. _Mimesis: https://https://mimesis.name/
.. _Custom Providers: https://mimesis.name/getting_started.html#custom-providers
.. _Arithmetic Parser User Guide: https://github.com/pyparsing/plusminus/blob/master/doc/arithmetic_parser_user_guide.md
