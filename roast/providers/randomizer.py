#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import inspect
import logging
import time
import numpy as np
from enum import Enum
from collections import Counter, defaultdict
from typing import Any, List, Type, Sequence
from mimesis import BaseDataProvider, BaseProvider, Choice, Development
from roast.providers.choices import Choices
from roast.providers.shuffle import Shuffle
from roast.utils import read_json, write_json, frange, mkfile, to_nested
from box import Box, BoxKeyError
from plusminus import ArithmeticParser
import pyparsing as pp
from roast.exceptions import RandomizerError

try:
    # For python 3.8 and later
    from mimesis.types import Seed
except ImportError:
    # For everyone else
    from mimesis.typing import Seed

__all__ = ["Randomizer"]

log = logging.getLogger(__name__)


class WeightPreset(Enum):
    LOW_HEAVY = 0
    HIGH_HEAVY = 1
    NORMAL = 2
    INVERSE_NORMAL = 3
    EXTREME_LIMITS = 4


class Randomizer(BaseDataProvider):
    def __init__(self, seed: Seed = None, randomize: bool = True) -> None:
        """Class that contains core Xilinx randomization data providers - `choice`,
        `choices`, `shuffle`, and `boolean`.

        The methods included provide complex randomization functionality based on core providers.

        A `data` attribute holds values randomly generated.

        Args:
            seed (Seed, optional): Seed for random. When set to `None` the current system time is
                used. Defaults to None.
            randomize (bool, optional): Retrieve randomized or default value. Defaults to True.
        """

        if seed is None:
            seed = int(time.time() * 1000)  # system time
        super().__init__(seed=seed)
        self.choice = Choice(seed=self.seed)
        self.choices = Choices(seed=self.seed)
        self.shuffle = Shuffle(seed=self.seed)
        self.boolean = Development(seed=self.seed).boolean
        self.randomize = randomize
        self.parser = ArithmeticParser()
        self.evaluate = self.parser.evaluate
        log.debug(f"seed={self.seed}")
        self.data = Box(
            conversion_box=False, default_box=True, default_box_attr=[], box_dots=True
        )
        self.replace = True
        self._excludes_file = ""
        self.rng = np.random.default_rng(seed)
        self.weights = defaultdict(list)

    @property
    def datafile(self):
        return self._datafile

    @datafile.setter
    def datafile(self, filename):
        self._datafile = filename
        _parameters = read_json(self._datafile, decode_numbers=True)
        self.parameters = Box(_parameters, box_dots=True)

    @property
    def excludes_file(self):
        return self._excludes_file

    @excludes_file.setter
    def excludes_file(self, filename):
        self._excludes_file = filename
        try:
            _data = read_json(filename, decode_numbers=True)
        except:
            mkfile(filename)
            _data = {}
        self.data = Box(
            _data,
            conversion_box=False,
            default_box=True,
            default_box_attr=[],
            box_dots=True,
        )
        self.replace = False

    def reset_excluded(self, attribute: str = "") -> None:
        if not attribute:
            self.data = {}
        elif not self.excludes_file:
            self.data[attribute] = []
        else:
            try:
                _json = read_json(self.excludes_file, decode_numbers=True)
            except ValueError:
                _json = {}
            _data = Box(_json, box_dots=True)
            if _data:
                _data[attribute] = []
            self.data[attribute] = []
        self.to_json()

    def to_json(self, filename="") -> None:
        """Dumps `data` attribute to JSON file. If filename is not specified, the filename set the
        through the excludes_file method will be used.

        Args:
            filename (str, optional): Filename where JSON data will be written. Defaults to "".
        """
        if filename:
            write_json(filename, to_nested(self.data))
        elif self.excludes_file:
            write_json(self.excludes_file, to_nested(self.data))

    def generate_weights(
        self, length, a: int = 1, b: int = 1, preset: WeightPreset = None
    ) -> Sequence[float]:
        """Generates a histogram over length-1 bins defined by the Beta probability distribution
        function. If defaults values are used, this is equivalent to a uniform distribution.

        Args:
            length (int): Number of weights
            a (int, optional): Alpha shape parameter. Defaults to 1.
            b (int, optional): Beta shape parameter. Defaults to 1.
            preset (WeightPreset, optional): Predefined Alpha and Beta values. Defaults to None.

        Returns:
            Sequence[float]: Relative weights.
        """
        if preset == WeightPreset.LOW_HEAVY:
            a = 1
            b = 10
        elif preset == WeightPreset.HIGH_HEAVY:
            a = 10
            b = 1
        elif preset == WeightPreset.NORMAL:
            a = 5
            b = 5
        elif preset == WeightPreset.INVERSE_NORMAL:
            a = 0.5
            b = 0.5
        elif preset == WeightPreset.EXTREME_LIMITS:
            a = 0.1
            b = 0.1
        try:
            p = self.rng.beta(a, b, length * 100)  # generate elements over distribution
            s = self.rng.binomial(length - 1, p)  # divide into bins
            c = Counter(s)  # count number of occurrences for each bin
            keys, weights = zip(
                *sorted(c.items())
            )  # sort ascending and extract bin number and weight
            if len(c) != length:  # interpolate if any bins are missing
                weights = np.interp(range(length), keys, weights)
        except MemoryError as e:
            log.error(e)
            raise
        return weights

    def check_attribute(self, attribute: str) -> None:
        """Checks if attribute exists in parameters.

        Args:
            attribute (str): Attribute name.

        Raises:
            KeyError: Exception raised if attribute not found.
        """
        try:
            self.parameters[attribute]
        except BoxKeyError:
            err_msg = f"Attribute {attribute} not defined."
            log.error(err_msg)
            raise KeyError(err_msg)

    def generate_attribute_weights(
        self, attribute: str, a: float = 1, b: float = 1, preset: WeightPreset = None
    ) -> None:
        """Generates weights for attribute and cached in memory to avoid regeneration.

        Args:
            attribute (str): Attribute name.
            a (int, optional): Alpha shape parameter. Defaults to 1.
            b (int, optional): Beta shape parameter. Defaults to 1.
            preset (WeightPreset, optional): Predefined Alpha and Beta values. Defaults to None.
        """
        excluded = self.get_excluded(attribute)
        elements = self.get_elements(attribute)
        weights = list(self.generate_weights(len(elements), a, b, preset))
        indices = sorted(
            [elements.index(exclude_element) for exclude_element in excluded]
        )
        for index in indices:
            del weights[index]
        self.weights[attribute] = weights

    def get_excluded(self, attribute: str) -> Sequence[Any]:
        """If global replacement or parameter replamcent is disabled, construct
        the sequence of elements to be excluded from selection. The parameter setting
        always overrides the global setting.

        Args:
            attribute (str): Attribute name.

        Returns:
            Sequence[Any]: Elements to be excluded from selection.
        """
        self.check_attribute(attribute)
        param_replace = self.parameters[attribute].get("replace")
        try:
            if (self.replace and param_replace is None) or param_replace:
                excluded = self.parameters[f"{attribute}.excluded"]
            else:
                excluded = list(self.parameters[f"{attribute}.excluded"]) + list(
                    self.data[attribute]
                )
        except KeyError:
            if (self.replace and param_replace is None) or param_replace:
                excluded = []
            else:
                excluded = self.data[attribute]
        return excluded

    def get_elements(self, attribute: str) -> List[Any]:
        """Constructs list of elements for possible selection. Either elements or range must
        exist or an exception will be thrown. If both exist, elements has precedence.

        Args:
            attribute (str): Attribute name.

        Raises:
            KeyError: Raised when neither elements nor range is defined.

        Returns:
            Sequence[Any]: List of elements for possible selection.
        """
        self.check_attribute(attribute)
        if "elements" in self.parameters[attribute]:
            elements = self.parameters[f"{attribute}.elements"]
        elif "range" in self.parameters[attribute]:
            elements = list(frange(*self.parameters[f"{attribute}.range"]))
        else:
            err_msg = f"For attribute {attribute}, elements or range not defined."
            log.error(err_msg)
            raise KeyError(err_msg)
        return elements

    def get_value(
        self, attribute: str, store_data: bool = True, preset=None, **kwargs
    ) -> Any:
        """Gets a randomized value defined by attribute name. Possible values can be discrete
        values or range with excluded values removed.

        Args:
            attribute (str): Dot-based key name to retrieve value.
            store_data (bool, optional): Store randomized value to `data` attribute. Defaults to
            True.
            preset (WeightPreset, optional): Predefined Alpha and Beta values. Defaults to None.
            kwargs: Keyword arguments for shape parameters.

        Returns:
            Random choice of possible elements if randomize is True.
            Default value if randomize is False.

        Raises:
            KeyError: If `attribute` is not found in parameters.

        """
        self.check_attribute(attribute)
        param_replace = self.parameters[attribute].get("replace")
        if self.randomize and self.parameters[attribute].get("randomize", True):
            elements = self.get_all_values(attribute)
            # if preset or kwargs, generate weights for attribute
            if preset or "preset" in self.parameters[attribute]:
                if "preset" in self.parameters[attribute]:
                    param_preset = self.parameters[f"{attribute}.preset"]
                    preset = WeightPreset[param_preset]
                if not self.weights[attribute]:
                    self.generate_attribute_weights(attribute, preset=preset)
                element = self.choices(elements, self.weights[attribute])[0]
            elif kwargs or "shape" in self.parameters[attribute]:
                if "shape" in self.parameters[attribute]:
                    shape = self.parameters[f"{attribute}.shape"]
                    kwargs["a"] = shape[0]
                    kwargs["b"] = shape[1]
                if not self.weights[attribute]:
                    self.generate_attribute_weights(attribute, **kwargs)
                element = self.choices(elements, self.weights[attribute])[0]
            else:
                element = self.choice(elements)
            if store_data and element not in self.data[attribute]:
                self.data[attribute].append(element)
            # if excluding previous and weights have been generated, delete weight for selected element
            if (self.replace and param_replace is None) or param_replace:
                return element
            else:
                if preset or kwargs:
                    index = elements.index(element)
                    del self.weights[attribute][index]
            return element
        else:
            try:
                format = self.parameters[attribute].get("format")
                element = self.parameters[f"{attribute}.default"]
                if format:
                    return f"{element:{format}}"
                else:
                    return element
            except BoxKeyError:
                err_msg = f"Default value for {attribute} not defined."
                log.error(err_msg)
                raise KeyError(err_msg)

    def get_all_values(self, attribute: str) -> Sequence[Any]:
        """Gets all values defined by attribute name. Possible values can be discrete
        values or range with excluded values removed.

        Args:
            attribute (str): Dot-based key name to retrieve all values.

        Returns:
            List of all possible values with excluded values removed.

        Raises:
            KeyError: If `attribute` is not found in parameters.

        """
        excluded = self.get_excluded(attribute)
        elements = self.get_elements(attribute)
        elements = [element for element in elements if element not in excluded]
        format = self.parameters[attribute].get("format")
        if format:
            elements = [f"{element:{format}}" for element in elements]
        return elements

    def generate_sequence(self, expr, attrs, max_tries=200, **kwargs) -> dict:
        """Generate a sequence of values defined by expression in attribute order. Two variables,
        'prev' and 'current', are included to simplify the comparison. In order for the "current"
        value to be added, it must satisfy the expression condition compared to the "previous"
        value. However, any expression can be used to define the condition.

        Args:
            expr (str): Expression to determine whether value is added to output sequence.
            attrs (:obj:`list` of :obj:`str`): Attributes to retrieve randomized values.
            max_tries (int, optional): Number of tries to generate random values. Defaults to 200.
            **kwargs: Keyword arguments to be declared into expression evaluation.

        Returns:
            dict: Randomized values defined by expression.

        Raises:
            Exception: If max_tries is reached without generating valid sequence.

        """
        expr_underscore = expr.replace(
            ".", "__"
        )  # Convert dot-based keys to double underscore
        _data = {}

        # Push kwargs to evaluate engine
        for key, value in kwargs.items():
            self.evaluate(f"{key} = {value}")

        for i in range(max_tries):
            try:
                for j, attr in enumerate(attrs):
                    if j == 0:
                        _data[attr] = self.get_value(attr, store_data=False)
                        attr_underscore = attr.replace(".", "__")
                        self.evaluate(f"{attr_underscore} = {_data[attr]}")
                        log.debug(f"i={i}, j={j}, data={_data}")
                    else:
                        for k in range(len(self.get_all_values(attr))):
                            _data[attr] = self.get_value(attr, store_data=False)
                            attr_underscore = attr.replace(".", "__")
                            self.evaluate(f"{attr_underscore} = {_data[attr]}")
                            log.debug(f"i={i}, j={j}, k={k}, data={_data}")
                            prev = _data[attrs[j - 1]]
                            self.evaluate(f"prev = {prev}")
                            current = _data[attr]
                            self.evaluate(f"current = {current}")
                            if self.evaluate(expr_underscore):
                                break
                        else:
                            raise Exception(f"Data generation failed for: {attr}")
                log.info("Data generation successful.")
                break
            except Exception as e:
                log.warning(e)
                continue
        else:
            raise RandomizerError(f"Data generation failed.")

        for key, value in _data.items():
            if value not in self.data[key]:
                self.data[key].append(value)
        return _data

    def generate_conditional(self, expr, max_tries=200, **kwargs) -> dict:
        """Generate randomized values defined by expression.

        Args:
            expr (str): Expression to determine whether value is added to output sequence.
            max_tries (int, optional): Number of tries to generate random values. Defaults to 200.
            **kwargs: Keyword arguments to be declared into expression evaluation.

        Returns:
            dict: Randomized values defined by expression.

        Raises:
            Exception: If max_tries is reached without generating valid sequence.

        """
        expr_underscore = expr.replace(
            ".", "__"
        )  # Convert dot-based keys to double underscore
        _data = {}

        # Push kwargs to evaluate engine
        for key, value in kwargs.items():
            self.evaluate(f"{key} = {value}")

        for i in range(max_tries):
            try:
                if self.evaluate(expr_underscore):
                    log.debug(f"expr: {expr}")
                    log.info("Data generation successful.")
                    self._clear_variables(_data)
                    break
                else:
                    raise Exception(f"Generated data failed condition: {expr}")
            except NameError as e:  # Missing variable is randomized attribute
                qs = pp.QuotedString("'")
                attr_underscore = qs.searchString(e)[0][0]
                attr = attr_underscore.replace("__", ".")
                _data[attr] = self.get_value(attr, store_data=False)
                self.evaluate(f"{attr_underscore} = {_data[attr]}")
                log.debug(f"i={i}, data={_data}")
            except Exception as e:
                log.warning(e)
                self._clear_variables(_data)
                continue
        else:
            raise RandomizerError(f"Data generation failed.")

        for key, value in _data.items():
            if value not in self.data[key]:
                self.data[key].append(value)
        return _data

    def _clear_variables(self, _data):
        for key in _data.keys():
            key_underscore = key.replace(".", "__")
            self.evaluate(f"{key_underscore} =")

    class Meta:
        """Class for metadata."""

        name = "randomizer"

    def __dir__(self) -> List[str]:
        """Available data providers.

        The list of result will be used in AbstractField to
        determine method's class.

        :return: List of attributes.
        """
        attributes = []
        exclude = BaseDataProvider().__dict__.keys()

        for a in self.__dict__:
            if a not in exclude:
                if a.startswith("_"):
                    attribute = a.replace("_", "", 1)
                    attributes.append(attribute)
                else:
                    attributes.append(a)
        return attributes

    def add_provider(self, cls: Type[BaseProvider]) -> None:
        """Add a custom provider to Generic() object.

        :param cls: Custom provider.
        :return: None
        :raises TypeError: if cls is not class or is not a subclass
            of BaseProvider.
        """
        if inspect.isclass(cls):
            if not issubclass(cls, BaseProvider):
                raise TypeError("The provider must be a " "subclass of BaseProvider")
            try:
                meta = getattr(cls, "Meta")
                name = getattr(meta, "name")
            except AttributeError:
                name = cls.__name__.lower()
            setattr(self, name, cls(seed=self.seed))
        else:
            raise TypeError("The provider must be a class")

    def add_providers(self, *providers: Type[BaseProvider]) -> None:
        """Add a lot of custom providers to Generic() object.

        :param providers: Custom providers.
        :return: None
        """
        for provider in providers:
            self.add_provider(provider)
