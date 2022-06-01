#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from roast.utils import *  # pylint: disable=unused-wildcard-import
from roast.utils.roast_utils import overrides as overrides_func
import pytest
from box import Box
import os


def test_generate_conf_override_func():
    config = Box(default_box=True, box_dots=True)
    config.a.a = "A.A"
    config.a.b = "A.B"
    config.zcu102.a.a = "ZCU102.A.A"
    config.zcu102.a.b = "ZCU102.A.B"
    override = "zcu102"
    config = overrides_func(config, override)
    assert config["a.a"] == "ZCU102.A.A"
    assert config["a.b"] == "ZCU102.A.B"


def test_generate_conf_override_list_func(request):
    config = Box(default_box=True, box_dots=True)
    config.a.a = "A.A"
    config.a.b = "A.B"
    config.b.a = "B.A"
    config.b.b = "B.B"
    config.zcu102.a.a = "ZCU102.A.A"
    config.zcu102.a.b = "ZCU102.A.B"
    config.zynq.b.a = "ZYNQ.A.A"
    config.zynq.b.b = "ZYNQ.A.B"
    overrides = ["zynq", "zcu102"]
    config = overrides_func(config, overrides)
    assert config["a.a"] == "ZCU102.A.A"
    assert config["a.b"] == "ZCU102.A.B"
    assert config["b.a"] == "ZYNQ.A.A"
    assert config["b.b"] == "ZYNQ.A.B"


def test_is_dir_exception():
    with pytest.raises(
        DirectoryNotFoundError, match="No such directory exists: /some/random/dir"
    ):
        is_dir("/some/random/dir", silent_discard=False)


def test_is_file_exception():
    with pytest.raises(
        FileNotFoundError, match="No such file exists: /some/random/file.txt"
    ):
        is_file("/some/random/file.txt", silent_discard=False)


def test_replace_string_exception():
    with pytest.raises(
        FileNotFoundError, match="No such file exists: /some/random/file.txt"
    ):
        replace_string("/some/random/file.txt", "something", "something else")


def test_replace_line_exception():
    with pytest.raises(
        FileNotFoundError, match="No such file exists: /some/random/file.txt"
    ):
        replace_line("/some/random/file.txt", "something", "something else")


def test_git_clone_exception():
    with pytest.raises(GitError, match="Failed to clone myurl"):
        git_clone("myurl", "/some/path", "master")


def test_symlink_exception():
    with pytest.raises(
        Exception,
        match="/some/other_random/file.txt file or directory not found to symlink",
    ):
        symlink("/some/random/file.txt", "/some/other_random/file.txt")


def test_copy_data_exception(tmpdir):
    # Sample src file for positive test
    sample_file = os.path.realpath(__file__)
    # Sample src dir for positive test
    sample_dir = os.path.dirname(sample_file)
    # Sample src path for testing exception
    random_file = "/some/random/file.txt"
    # Below two are positive test scenarios
    copy_data(sample_file, tmpdir)
    copy_data(sample_dir, tmpdir)
    # Below two are negative test scenarios
    copy_data(random_file, tmpdir)
    with pytest.raises(ValueError):
        copy_data(random_file, tmpdir, silent_discard=False)
