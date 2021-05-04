.. _data-provider:

==========================
 Randomized Data Provider
==========================

The randomized data provider within ROAST is a data generator based on the `Mimesis`_ open source
library.

The generated data can be used to define a range of values or a set of discrete values for a
parameter of a component. Examples include:

- Clock divider where the value can be from 3 to 7
- Bus data width where the value can be 32, 64, or 128 bits

In addition to providing possible values, a random choice can also be selected.

Interfaces are included for the creation of custom providers that can generate data for any
scenario.

Randomizer Provider
===================

A generic randomizer is included however it does not include any providers. The randomizer
interface provides a method to use seeded data and add custom providers.

.. code-block:: python

    from roast.providers.randomizer import Randomizer
    
    randomizer = Randomizer(seed=0)
    randomizer.add_provider(MyProvider)

Custom Providers
================

Custom providers will need to be created to generate data for specific usage. Here is a custom
provider that will load a JSON parameter file into a dictionary and return a random choice
based on spefied parameter.

.. code-block:: python

    import json
    from mimesis import BaseDataProvider
    from roast.providers.randomizer import Randomizer

    class MyProvider(BaseDataProvider):
        def __init__(self, seed, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self.seed = seed
            self.r = Randomizer(seed=self.seed)

        class Meta:
            name = "my_provider"

        @property
        def parameter_file(self):
            return self._parameter_file

        @parameter_file.setter
        def parameter_file(self, file):
            self._parameter_file = file
            self.parameters = json.load(self._parameter_file)

        def pick_parameter_value(self, parameter):
            parameter_choices = self.parameters[parameter]
            return self.r.choice(parameter_choices)

This can be used as such:

.. code-block:: python

    import roast.providers.randomizer import Randomizer
    import MyProvider

    def MyClass:
        def __init__(self):
            self._randomizer = Randomizer(seed=0)
            self._randomizer.add_provider(MyProvider)
            self.randomizer = self._randomizer.my_provider
            self.randomizer.parameter_file = "my_parameters.json"

        def get_random_parameter_value(self, parameter):
            return self.randomizer.pick_parameter_value(parameter)


.. _Mimesis: https://https://mimesis.name/
