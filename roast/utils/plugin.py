#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import logging
import pkg_resources

log = logging.getLogger(__name__)


def register_plugin(location, name, plugin_type, entry_point) -> None:
    """Registers a plugin to the global working_set instance without needing to install.

    Args:
        location (str): Full path to file that might be used on sys.path.
        name (str): Name of plugin to be referenced.
        plugin_type (str): Type to determine plugin namespace.
        entry_point (str): Entry point in the form: some.module:some.attr

    Raises:
        Exception: Raised when plugin_type is not supported.
    """
    distribution = pkg_resources.Distribution(location=location, project_name=name)
    distribution._ep_map = {}
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

    ep = pkg_resources.EntryPoint.parse(f"{name} = {entry_point}", dist=distribution)
    distribution._ep_map.update({namespace: {name: ep}})
    pkg_resources.working_set.add(distribution)
