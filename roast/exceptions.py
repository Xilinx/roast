#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#


import logging

log = logging.getLogger(__name__)


class RoastError(Exception):
    """
    The base exception class for all roast exceptions.
    """

    def __init__(self, message: str = None, log_stack: bool = False) -> None:
        self.message = message or getattr(self.__class__, "message", None)
        super().__init__(message)
        if log_stack:
            log.exception(message)
        else:
            log.error(message)

    def __str__(self):
        return self.message


class DirectoryNotFoundError(RoastError):
    """
    Raised when directory is not found in roast utils.
    """


class GitError(RoastError):
    """
    Raised when a Git error occurs in roast utils.
    """


class ExpectError(RoastError):
    """
    Raised when EOF or TIMEOUT occurs in Xexpect.
    """


class PluginError(RoastError):
    """
    Raised when plugin type is not supported in roast.
    """


class RandomizerError(RoastError):
    """
    Raised when Randomizer failed data generation.
    """
