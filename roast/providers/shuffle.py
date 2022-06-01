#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

"""Provides a shuffled sequence from items in a sequence."""
import collections.abc
from typing import Any, List, Optional, Sequence, Union

from mimesis.providers.base import BaseProvider

__all__ = ["Shuffle"]


class Shuffle(BaseProvider):
    """Class for generating a shuffled sequence from items in a sequence."""

    class Meta:
        """Class for metadata."""

        name = "shuffle"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize attributes.

        :param args: Arguments.
        :param kwargs: Keyword arguments.
        """
        super().__init__(*args, **kwargs)

    def __call__(
        self,
        items: Optional[Sequence[Any]],
        essential: Optional[Sequence[Any]] = None,
        length: int = 0,
    ) -> Sequence[Any]:
        """Generate a shuffled sequence from a sequence.

        Provide a shuffled sequence from the elements in a sequence
        **items**, where selections must include elements in **essential** when
        it is specified. If not specified, a plain shuffle is returned.

        :param items: Non-empty sequence (list, tuple or string) of elements.
        :param essential: Non-empty sequence (list, tuple or string) of elements.
        :param length: Length of sequence (number of elements) to provide.
        :return: Sequence chosen from items.
        :raises TypeError: For non-sequence items.
        :raises ValueError: If negative length.

        >>> from roast.providers.shuffle import Shuffle
        >>> shuffle = Shuffle()
        >>> shuffle(items=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        [8, 4, 2, 10, 7, 6, 9, 3, 1, 5]
        >>> shuffle(items=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10), length=7)
        (1, 5, 10, 8, 2, 4, 6)
        >>> shuffle(items=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], essential=[3, 6, 9])
        [2, 9, 5, 7, 3, 6, 8]
        >>> shuffle(items=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10), essential=[3, 6, 9], length=5)
        (5, 6, 7, 3, 9)
        """

        if not isinstance(items, collections.abc.Sequence):
            raise TypeError("**items** must be non-empty sequence.")

        if not items:
            raise ValueError("**items** must be a non-empty sequence.")

        data: List = []
        if essential is None:
            if length == 0:
                data = list(items)
                self.random.shuffle(data)
            else:
                data = self.random.sample(items, k=length)
        else:
            if len(set(items)) < length:  # avoid an infinite while loop
                raise ValueError(
                    "There are not enough unique elements in "
                    "**items** to provide the specified **number**."
                )
            for element in essential:
                if element in items:
                    continue
                else:
                    raise ValueError(
                        "All elements in **essential** must exist in **items**."
                    )
            if length == 0:
                length = self.random.randint(len(essential), len(items))
            data = list(essential)
            while len(data) < length:
                item = self.random.choice(items)
                if item not in data:
                    data.append(item)
            self.random.shuffle(data)

        if isinstance(items, list):
            return data
        elif isinstance(items, tuple):
            return tuple(data)
        return "".join(data)
