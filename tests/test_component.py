#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import pkg_resources
from roast.component.scenario import scenario
from roast.component.system import SystemBase
from roast.component.testsuite import TestSuiteBase
from roast.confParser import generate_conf
from roast.utils import register_plugin


class DummySystem(SystemBase):
    def __init__(self, config):
        super().__init__(config)

    def configure(self):
        self.configured = True

    def build(self):
        return True


class DummyTestSuite(TestSuiteBase):
    def __init__(self, config):
        super().__init__(config)

    def configure(self):
        self.configured = True

    def build(self):
        return True

    def deploy(self):
        return True

    def run(self):
        return True


def test_component_interface(request):
    ts_name = "dummy_ts"
    sys_name = "dummy_sys"
    register_plugin(ts_name, "testsuite", "tests.test_component:DummyTestSuite")
    register_plugin(sys_name, "system", "tests.test_component:DummySystem")

    rootdir = request.config.rootdir.strpath
    fspath = request.node.fspath
    test_name = request.node.name
    config = generate_conf(rootdir, fspath, test_name)
    config["roast.testsuite"] = ts_name
    config["roast.system"] = [sys_name]
    scn = scenario(config)
    scn.configure_component()
    ts = scn.ts
    sys = scn.sys(sys_name)
    assert ts.configured == True
    assert sys.configured == True

    results = scn.build_component()
    assert results[ts_name] == True
    assert results[sys_name] == True

    results = scn.deploy_component()
    assert results[ts_name] == True

    results = scn.run_component()
    assert results[ts_name] == True
