#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import inspect
from typing import Any, List, Type
from mimesis import BaseDataProvider, BaseProvider, Choice

__all__ = ["Randomizer"]


class Randomizer(BaseDataProvider):
    """Class that contains only Xilinx providers."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize attributes lazily.

        :param args: Arguments.
        :param kwargs: Keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.choice = Choice(seed=self.seed)

    class Meta:
        """Class for metadata."""

        name = "generic"

    def __getattr__(self, attrname: str) -> Any:
        """Get attribute without underscore.

        :param attrname: Attribute name.
        :return: An attribute.
        """
        attribute = object.__getattribute__(self, "_" + attrname)
        if attribute and callable(attribute):
            self.__dict__[attrname] = attribute(
                self.locale,
                self.seed,
            )
            return self.__dict__[attrname]

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
