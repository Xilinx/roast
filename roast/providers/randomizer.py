#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import inspect
import logging
from typing import Any, List, Type
from mimesis import BaseDataProvider, BaseProvider, Choice, Development
from roast.providers.choices import Choices
from roast.utils import read_json, frange
from box import Box, BoxError
from plusminus import ArithmeticParser
import pyparsing as pp
from roast.exceptions import RandomizerError

__all__ = ["Randomizer"]

log = logging.getLogger(__name__)


class Randomizer(BaseDataProvider):
    """Class that contains only Xilinx providers."""

    def __init__(self, randomize=True, *args, **kwargs) -> None:
        """Initialize attributes lazily.

        Args:
            randomize (bool): Boolean parameter to retrieve randomize or default value. Defaults
                to True.
            *args: Arguments.
            **kwargs: Keyword arguments.

        """
        super().__init__(*args, **kwargs)
        self.choice = Choice(seed=self.seed)
        self.choices = Choices(seed=self.seed)
        self.boolean = Development(seed=self.seed).boolean
        self.randomize = randomize
        self.parser = ArithmeticParser()
        self.evaluate = self.parser.evaluate
        log.debug(f"seed={self.seed}")

    @property
    def datafile(self):
        return self._datafile

    @datafile.setter
    def datafile(self, file):
        self._datafile = file
        _parameters = read_json(self._datafile)
        self.parameters = Box(_parameters, box_dots=True)

    def get_value(self, attribute: str):
        """Gets a randomized value defined by attribute name. Possible values can be discrete
        values or range with excluded values removed.

        Args:
            attribute (str): Dot-based key name to retrieve value.

        Returns:
            Random choice of possible elements if randomize is True.
            Default value if randomize is False.

        Raises:
            KeyError: If `attribute` is not found in parameters.

        """
        if self.randomize:
            try:
                excluded = self.parameters[f"{attribute}.excluded"]
            except KeyError:
                excluded = []
            except BoxError:
                err_msg = f"Attribute {attribute} not defined."
                log.error(err_msg)
                raise KeyError(err_msg)
            if "values" in self.parameters[attribute]:
                values = self.parameters[f"{attribute}.values"]
                elements = [value for value in values if value not in excluded]
            elif "range" in self.parameters[attribute]:
                elements = [
                    value
                    for value in frange(*self.parameters[f"{attribute}.range"])
                    if value not in excluded
                ]
            else:
                err_msg = f"For attrbiute {attribute}, values or range not defined."
                log.error(err_msg)
                raise KeyError(err_msg)
            return self.choice(elements)
        else:
            return self.parameters[f"{attribute}.default"]

    def get_all_values(self, attribute: str) -> list:
        """Gets all values defined by attribute name. Possible values can be discrete
        values or range with excluded values removed.

        Args:
            attribute (str): Dot-based key name to retrieve all values.

        Returns:
            List of all possible values with excluded values removed.

        Raises:
            KeyError: If `attribute` is not found in parameters.

        """
        try:
            excluded = self.parameters[f"{attribute}.excluded"]
        except KeyError:
            excluded = []
        except BoxError:
            err_msg = f"Attribute {attribute} not defined."
            log.error(err_msg)
            raise KeyError(err_msg)
        if "values" in self.parameters[attribute]:
            values = self.parameters[f"{attribute}.values"]
            elements = [value for value in values if value not in excluded]
        elif "range" in self.parameters[attribute]:
            elements = [
                value
                for value in frange(*self.parameters[f"{attribute}.range"])
                if value not in excluded
            ]
        else:
            err_msg = f"For attrbiute {attribute}, values or range not defined."
            log.error(err_msg)
            raise KeyError(err_msg)
        return elements

    def generate_sequence(self, expr, attrs, max_tries=200, **kwargs):
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
        data = {}

        # Push kwargs to evaluate engine
        for key, value in kwargs.items():
            self.evaluate(f"{key} = {value}")

        for i in range(max_tries):
            try:
                for j, attr in enumerate(attrs):
                    if j == 0:
                        data[attr] = self.get_value(attr)
                        attr_underscore = attr.replace(".", "__")
                        self.evaluate(f"{attr_underscore} = {data[attr]}")
                        log.debug(f"i={i}, j={j}, data={data}")
                    else:
                        for k in range(len(self.get_all_values(attr))):
                            data[attr] = self.get_value(attr)
                            attr_underscore = attr.replace(".", "__")
                            self.evaluate(f"{attr_underscore} = {data[attr]}")
                            log.debug(f"i={i}, j={j}, k={k}, data={data}")
                            prev = data[attrs[j - 1]]
                            self.evaluate(f"prev = {prev}")
                            current = data[attr]
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

        return data

    def generate_conditional(self, expr, max_tries=200, **kwargs):
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
        data = {}

        # Push kwargs to evaluate engine
        for key, value in kwargs.items():
            self.evaluate(f"{key} = {value}")

        for i in range(max_tries):
            try:
                if self.evaluate(expr_underscore):
                    log.debug(f"expr: {expr}")
                    log.info("Data generation successful.")
                    self._clear_variables(data)
                    break
                else:
                    raise Exception(f"Generated data failed condition: {expr}")
            except NameError as e:  # Missing variable is randomized attribute
                qs = pp.QuotedString("'")
                attr_underscore = qs.searchString(e)[0][0]
                attr = attr_underscore.replace("__", ".")
                data[attr] = self.get_value(attr)
                self.evaluate(f"{attr_underscore} = {data[attr]}")
                log.debug(f"i={i}, data={data}")
            except Exception as e:
                log.warning(e)
                self._clear_variables(data)
                continue
        else:
            raise RandomizerError(f"Data generation failed.")

        return data

    def _clear_variables(self, data):
        for key in data.keys():
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
