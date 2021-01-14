#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import inspect
import pytest
from roast.confParser import generate_conf, get_machine_file


def test_generate_conf_plain(request):
    rootdir = request.config.rootdir.strpath
    fspath = request.node.fspath
    test_name = request.node.name
    config = generate_conf(rootdir, fspath, test_name)
    assert config["ROOT"] == rootdir
    assert config["build"] == "2020.2_daily_latest"
    config["version"] = "2019.2"
    assert config["build"] == "2019.2_daily_latest"
    assert config["mylist"] == ["a", "b"]


def test_generate_conf_list_override(request):
    rootdir = request.config.rootdir.strpath
    fspath = request.node.fspath
    test_name = request.node.name
    overrides = ["version=2019.2", "mylist=c,d"]
    config = generate_conf(rootdir, fspath, test_name, overrides=overrides)
    assert config["ROOT"] == rootdir
    assert config["build"] == "2019.2_daily_latest"
    assert config["mylist"] == ["c", "d"]


def test_generate_conf_file_override(request):
    rootdir = request.config.rootdir.strpath
    fspath = request.node.fspath
    test_name = request.node.name
    overrides = ["tests/main/conf.py"]
    config = generate_conf(rootdir, fspath, test_name, overrides=overrides)
    assert config["ROOT"] == rootdir
    assert config["build"] == "2019.2_daily_latest"
    assert config["mylist"] == ["c", "d"]


def test_generate_conf_params(request):
    rootdir = request.config.rootdir.strpath
    fspath = request.node.fspath
    test_name = "main"
    params = ["test1"]
    config = generate_conf(rootdir, fspath, test_name, params=params)
    assert config["ROOT"] == rootdir
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


def test_get_machine_file_exception(request):
    with pytest.raises(Exception, match="zinc"):
        get_machine_file("zinc")
