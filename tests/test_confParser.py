#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import inspect
import pytest
from roast.confParser import generate_conf, get_machine_file

overrides = ["a.b=2020.2", "tests/main/conf.py"]


def test_generate_conf_none():
    config = generate_conf()
    assert config["ROOT"] == os.getcwd()


def test_generate_conf_plain(request):
    rootdir = request.config.rootdir.strpath
    fspath = request.node.fspath
    test_name = request.node.name
    config = generate_conf(rootdir, fspath, test_name)
    assert config["ROOT"] == rootdir
    assert config["buildDir"] == os.path.join(rootdir, "build")
    ws_dir = os.path.join(rootdir, "build", "tests", test_name)
    assert config["wsDir"] == ws_dir
    assert config["logDir"] == os.path.join(ws_dir, "log")
    assert config["workDir"] == os.path.join(ws_dir, "work")
    assert config["imagesDir"] == os.path.join(ws_dir, "images")
    assert config["build"] == "2020.2_daily_latest"
    config["version"] = "2019.2"
    assert config["build"] == "2019.2_daily_latest"
    assert config["mylist"] == ["a", "b"]


def test_generate_conf_list_override(request):
    rootdir = request.config.rootdir.strpath
    fspath = request.node.fspath
    test_name = request.node.name
    overrides = ["version=2019.2", "mylist=c,d", "a.b=2020.2", "missingvar=hello"]
    config = generate_conf(rootdir, fspath, test_name, overrides=overrides)
    assert config["ROOT"] == rootdir
    assert config["build"] == "2019.2_daily_latest"
    assert config["mylist"] == ["c", "d"]
    assert config["a.b"] == "2020.2"
    assert config["missingvar"] == "hello"


def test_generate_conf_file_override(request):
    rootdir = request.config.rootdir.strpath
    fspath = request.node.fspath
    test_name = request.node.name
    overrides = ["tests/main/conf.py"]
    config = generate_conf(rootdir, fspath, test_name, overrides=overrides)
    assert config["ROOT"] == rootdir
    assert config["build"] == "2019.2_daily_latest"
    assert config["mylist"] == ["c", "d"]


@pytest.mark.parametrize("test", [0, 1])
def test_generate_conf_mixed_override(request, test):
    """This will test for mixed overrides and also ensure that overrides are not overwritten between test runs (#129)"""
    rootdir = request.config.rootdir.strpath
    fspath = request.node.fspath
    test_name = request.node.name
    config = generate_conf(rootdir, fspath, test_name, overrides=overrides)
    assert config["ROOT"] == rootdir
    assert config["build"] == "2019.2_daily_latest"
    assert config["mylist"] == ["c", "d"]
    assert config["a.b"] == "2020.2"


def test_generate_conf_params(request):
    rootdir = request.config.rootdir.strpath
    fspath = request.node.fspath
    test_name = "main"
    params = ["test1"]
    config = generate_conf(rootdir, fspath, test_name, params=params)
    assert config["ROOT"] == rootdir
    ws_dir = os.path.join(rootdir, "build", "tests", test_name, *params)
    assert config["wsDir"] == ws_dir
    assert config["mytest"] == "test1"


def test_generate_conf_machine(request, mocker):
    rootdir = request.config.rootdir.strpath
    fspath = request.node.fspath
    test_name = request.node.name
    config = generate_conf(rootdir, fspath, test_name)
    assert config["dtb_arch"] == "aarch64"
    machine_file = os.path.join(rootdir, "tests", "machines/zynq.py")
    mocker.patch("roast.confParser.get_machine_file", return_value=machine_file)
    config = generate_conf(rootdir, fspath, test_name, machine="zynq")
    assert config["dtb_arch"] == "arm"
    overrides = ["version=2019.2"]
    config = generate_conf(
        rootdir, fspath, test_name, overrides=overrides, machine="zynq"
    )
    ws_dir = os.path.join(rootdir, "build", "zynq", "tests", test_name)
    assert config["wsDir"] == ws_dir


def test_generate_conf_overrides_var(request, mocker):
    rootdir = request.config.rootdir.strpath
    fspath = request.node.fspath
    test_name = "main"
    params = ["test2"]
    overrides = ["version=2021.1"]
    config = generate_conf(
        rootdir,
        fspath,
        test_name,
        params=params,
        overrides=overrides,
    )
    assert config["mytest"] == "test2"  # params main/test1/conf.py
    assert config["build"] == "2021.1_daily_latest"  # from overrides
    assert config["mylist"] == ["c", "d"]  # main/conf.py
    assert config["b.a"] == "hello3"  # subtree override from main/test2/conf.py
    assert config["b.b"] == "hello again3"  # subtree override from main/test2/conf.py


def test_generate_conf_full(request, mocker):
    rootdir = request.config.rootdir.strpath
    fspath = request.node.fspath
    test_name = "main"
    params = ["test1"]
    overrides = ["version=2021.1", "mysubtree"]
    machine_file = os.path.join(rootdir, "tests", "machines/zynq.py")
    mocker.patch("roast.confParser.get_machine_file", return_value=machine_file)
    config = generate_conf(
        rootdir,
        fspath,
        test_name,
        params=params,
        overrides=overrides,
        machine="zynq",
    )
    assert config["mytest"] == "test1"  # params main/test1/conf.py
    assert config["dtb_arch"] == "arm"  # machine
    assert config["build"] == "2021.1_daily_latest"  # from overrides
    assert config["mylist"] == ["c", "d"]  # main/conf.py
    assert config["b.a"] == "hello2"  # subtree
    assert config["b.b"] == "hello again2"  # subtree
    ws_dir = os.path.join(rootdir, "build", "zynq", "tests", test_name, *params)
    assert config["wsDir"] == ws_dir


def test_get_machine_file_exception(request):
    with pytest.raises(FileNotFoundError, match="zinc"):
        get_machine_file("zinc")
