#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import pytest
from roast.confParser import generate_conf
from roast.component.basebuild import Basebuild


def test_basebuild_params(request, build_dir):
    rootdir = request.config.rootdir.strpath
    fspath = request.node.fspath
    test_name = "main"
    params = ["test1"]
    config = generate_conf(rootdir, fspath, test_name, params=params)
    config["buildDir"] = build_dir
    builder = Basebuild(config)
    builder.configure()
    assert os.path.exists(builder.workDir)
    assert os.path.exists(builder.imagesDir)
    assert os.path.exists(os.path.join(builder.workDir, "conf.py"))
    assert os.path.exists(os.path.join(builder.workDir, "test_dummy.py"))
    os.chdir(rootdir)  # reset working directory changed by Basebuild


def test_basebuild_base_params(request, build_dir):
    rootdir = request.config.rootdir.strpath
    fspath = request.node.fspath
    test_name = "main"
    base_params = ["base"]
    config = generate_conf(rootdir, fspath, test_name, base_params=base_params)
    config["buildDir"] = build_dir
    builder = Basebuild(config)
    builder.configure()
    assert builder.wsDir == os.path.join(
        config["buildDir"], *config["base_params"], *config["test_path_list"]
    )
    os.chdir(rootdir)  # reset working directory changed by Basebuild


def test_basebuild_build_exception(request):
    rootdir = request.config.rootdir.strpath
    fspath = request.node.fspath
    test_name = request.node.name
    config = generate_conf(rootdir, fspath, test_name)
    builder = Basebuild(config)
    with pytest.raises(NotImplementedError):
        builder.build()
    os.chdir(rootdir)  # reset working directory changed by Basebuild
