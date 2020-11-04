#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import re
import sys
import contextlib
import logging
import inspect
from importlib import import_module
from typing import Iterable, List
from config import config, ConfigurationSet, InterpolateEnumType
from roast.utils import *  # pylint: disable=unused-wildcard-import

log = logging.getLogger(__name__)


def load_configuration(
    modules: Iterable, interpolate_type=InterpolateEnumType.STANDARD
) -> ConfigurationSet:
    """This function loads configuration files heirarchically. The format types accepted are:
    py, json, ini, yaml, toml

    Args:
        modules (Iterable): configurations

    Returns:
        ConfigurationSet: layered configuration
    """
    cfg = config(
        *modules,
        separator="__",
        ignore_missing_paths=True,
        interpolate=True,
        interpolate_type=interpolate_type,
    )
    return cfg


def get_machine_file(machine: str) -> str:
    machine_file = ""
    if machine:
        module = f"roast.machines.{machine}"
        try:
            m = import_module(module)
            machine_file = inspect.getsourcefile(m)
        except ImportError:
            raise Exception(f"ERROR: '{machine}' is not a valid machine")
    return machine_file


def generate_conf(
    rootdir: str,
    test_path: str,
    test_name: str,
    base_params: Optional[List[str]] = None,
    params: Optional[List[str]] = None,
    overrides: Optional[List[str]] = None,
    machine: str = "",
    interpolate_type=InterpolateEnumType.STANDARD,
) -> ConfigurationSet:
    """Create a :obj:`ConfigurationSet` from a heirarchy of configuration files.

    Args:
        rootdir: The base directory.
        test_path: Full path of test file.
        test_name: Name for the test
        base_params: Optional parameters. Defaults to None.
        params: Optional parameters. Defaults to None.
        overrides: Optional key/value pairs to override generated configuration. Defaults to None.
        machine: Optional machine type to override configuration.

    Returns:
        Layered configuration with lowest level taking precedence.
    """
    if base_params is None:
        base_params = []
    if params is None:
        params = []
    if overrides is None:
        overrides = []
    relpath = os.path.relpath(test_path, rootdir)
    relpath_list = relpath.split(os.sep)
    del relpath_list[-1]  # remove file name from list
    relpath_list.append(test_name)
    relpath_param_list = relpath_list + params

    # Build list of configuration files by iterating each dir level
    supported_extensions = [
        ".py",
        ".ini",
        ".toml",
        ".json",
        ".yaml",
        ".yml",
    ]
    relative_path = ""
    config_list = []
    for relpath_param in ["."] + relpath_param_list:  # start with rootdir
        relative_path = os.path.abspath(os.path.join(relative_path, relpath_param))
        search_dir = os.path.join(rootdir, relative_path)
        with contextlib.suppress(FileNotFoundError):
            for filename in os.listdir(search_dir):
                root, ext = os.path.splitext(filename)
                if root == "conf" and ext in supported_extensions:
                    found_conf = os.path.join(search_dir, filename)
                    log.debug(f"Configuration file found at {found_conf}")
                    config_list.append(found_conf)

    if machine:
        config_list.append(get_machine_file(machine))

    # Override files
    for index, override in enumerate(overrides):
        _, ext = os.path.splitext(override)
        if "=" not in override and ext in supported_extensions:
            override_abspath = os.path.abspath(override)
            if is_file(override_abspath):
                log.debug(f"Override configuration file found at {override_abspath}")
                config_list.append(override_abspath)
                del overrides[index]

    # Load list of configuration files into config
    config_list.reverse()  # Lowest level first and takes precedence
    config = load_configuration(config_list, interpolate_type=interpolate_type)

    # Override variables
    for override in overrides:
        key, value = override.split("=")
        if has_key(config.as_dict(), key):
            if type(config[key]) is list:
                value = value.split(",")
        log.debug(f"Override variable applied: {key}: {value}")
        config.update({key: value})

    config["ROOT"] = rootdir
    config["testSuite"] = relpath_list[0]
    config["test"] = test_name
    config["test_path_list"] = relpath_list
    config["test_param_path_list"] = relpath_param_list
    config["test_path"] = os.path.join(rootdir, *relpath_list)
    config["base_params"] = base_params
    config["params"] = params

    if machine:
        config["machine"] = machine
        base_params.insert(0, machine)
        config["base_params"] = base_params

    return config
