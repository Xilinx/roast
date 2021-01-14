#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

try:
    # For python 3.8 and later
    import importlib.metadata as importlib_metadata
except ImportError:
    # For everyone else
    import importlib_metadata

import logging
from stevedore import ExtensionManager

log = logging.getLogger(__name__)


def register_plugin(name, plugin_type, entry_point) -> None:
    """Registers a plugin dynamically without needing to install as a package.

    Args:
        name (str): Name of plugin to be referenced.
        plugin_type (str): Type to determine plugin namespace.
        entry_point (str): Entry point in the form: some.module:some.attr

    Raises:
        Exception: Raised when plugin_type is not supported.
    """
    if plugin_type == "system":
        namespace = "roast.component.system"
    elif plugin_type == "testsuite":
        namespace = "roast.component.testsuite"
    elif plugin_type == "serial":
        namespace = "roast.serial"
    elif plugin_type == "board":
        namespace = "roast.board"
    elif plugin_type == "relay":
        namespace = "roast.relay"
    else:
        err_msg = f"Plugin type {plugin_type} is not supported."
        log.error(err_msg)
        raise Exception(err_msg)

    ep = importlib_metadata.EntryPoint(name, entry_point, namespace)
    e = ExtensionManager(namespace)
    if namespace in e.ENTRY_POINT_CACHE:
        entry_points = e.ENTRY_POINT_CACHE.get(namespace)
        if name not in [entry_point.name for entry_point in entry_points]:
            entry_points.append(ep)
            e.ENTRY_POINT_CACHE[namespace] = entry_points
    else:
        e.ENTRY_POINT_CACHE[namespace] = [ep]
    ep.load()
