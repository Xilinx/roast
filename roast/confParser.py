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
from roast.utils import overrides as overrides_func

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
    rootdir: Optional[str] = None,
    test_path: str = "",
    test_name: str = "",
    base_params: Optional[List[str]] = None,
    params: Optional[List[str]] = None,
    overrides: Optional[List[str]] = None,
    machine: str = "",
    interpolate_type=InterpolateEnumType.STANDARD,
) -> ConfigurationSet:
    """Create a :obj:`ConfigurationSet` from a heirarchy of configuration files.

    Args:
        rootdir: The base directory. Defaults to None.
        test_path: Full path of test file. Defaults to empty string.
        test_name: Name for the test. Defaults to empty string.
        base_params: Optional parameters. Defaults to None.
        params: Optional parameters. Defaults to None.
        overrides: Optional key/value pairs to override generated configuration. Defaults to None.
        machine: Optional machine type to override configuration.

    Returns:
        Layered configuration with lowest level taking precedence.
    """

    if rootdir is None:
        rootdir = os.getcwd()
        test_path = inspect.stack()[1][1]
        test_name = inspect.stack()[1][3]
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

    for relpath_param in [rootdir] + relpath_param_list:  # start with rootdir
        relative_path = os.path.abspath(os.path.join(relative_path, relpath_param))
        search_dir = os.path.join(rootdir, relative_path)
        with contextlib.suppress(FileNotFoundError):
            for filename in os.listdir(search_dir):
                root, ext = os.path.splitext(filename)
                if root == "conf" and ext in supported_extensions:
                    found_conf = os.path.join(search_dir, filename)
                    log.debug(f"Configuration file found at {found_conf}")
                    config_list.append(found_conf)

    file_overrides = []
    var_overrides = []
    subtree_overrides = []
    for override in overrides:
        _, ext = os.path.splitext(override)
        if "=" not in override:
            if ext in supported_extensions:
                file_overrides.append(override)
            else:
                subtree_overrides.append(override)
        elif "=" in override and ext not in supported_extensions:
            var_overrides.append(override)

    # Override files
    for override in file_overrides:
        override_abspath = os.path.abspath(override)
        if is_file(override_abspath):
            log.debug(f"Override configuration file found at {override_abspath}")
            config_list.append(override_abspath)

    # Base configuration parameters
    build_dir = os.path.join(rootdir, "build")
    base_ws_dir = os.path.join(build_dir, *base_params)
    test_base_ws_dir = os.path.join(build_dir, *base_params, *relpath_list)
    ws_dir = os.path.join(build_dir, *base_params, *relpath_list, *params)
    log_dir = os.path.join(ws_dir, "log")
    work_dir = os.path.join(ws_dir, "work")
    images_dir = os.path.join(ws_dir, "images")

    base_config = {
        "ROOT": rootdir,
        "buildDir": build_dir,
        "testSuite": relpath_list[0],
        "test": test_name,
        "test_path_list": relpath_list,
        "test_param_path_list": relpath_param_list,
        "test_path": os.path.join(rootdir, *relpath_list),
        "base_params": base_params,
        "params": params,
        "wsDir": ws_dir,
        "logDir": log_dir,
        "workDir": work_dir,
        "imagesDir": images_dir,
        "base_ws_dir": base_ws_dir,
        "test_base_ws_dir": test_base_ws_dir,
    }
    config_list.append(base_config)  # type: ignore

    if machine:  # base_params and downstream vars need to be updated
        base_params.insert(0, machine)
        base_ws_dir = os.path.join(build_dir, *base_params)
        test_base_ws_dir = os.path.join(build_dir, *base_params, *relpath_list)
        ws_dir = os.path.join(build_dir, *base_params, *relpath_list, *params)
        log_dir = os.path.join(ws_dir, "log")
        work_dir = os.path.join(ws_dir, "work")
        images_dir = os.path.join(ws_dir, "images")
        subtree_overrides.insert(0, machine)
        machine_config = {
            "machine": machine,
            "base_params": base_params,
            "wsDir": ws_dir,
            "logDir": log_dir,
            "workDir": work_dir,
            "imagesDir": images_dir,
            "base_ws_dir": base_ws_dir,
            "test_base_ws_dir": test_base_ws_dir,
        }
        config_list.append(machine_config)  # type: ignore
        config_list.append(get_machine_file(machine))

    config_list.reverse()  # Lowest level first and takes precedence
    config = load_configuration(config_list, interpolate_type=interpolate_type)

    # append override variable from config to overrides at highest level and takes precedence
    if config.get("overrides"):
        if type(config["overrides"]) is list:
            subtree_overrides = config["overrides"] + subtree_overrides  # type: ignore
        else:
            log.error(
                "Override variable detected but should be of type list not : {}".format(
                    type(config["overrides"])
                )
            )

    # auto override variables in configuration
    if subtree_overrides:
        for override in subtree_overrides:
            overrides_func(config, override)
            log.debug(f"Subtree overrides variable applied: {override}")

    # Override variables
    for override in var_overrides:
        key, value = override.split("=")
        if key in config:
            if type(config.as_dict()[key]) is list:
                value = value.split(",")
        log.debug(f"Override variable applied: {key}: {value}")
        config.update({key: value})

    return config
