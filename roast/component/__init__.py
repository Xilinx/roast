#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from abc import ABCMeta, abstractmethod
from stevedore import driver, named


class ComponentFactory(metaclass=ABCMeta):
    """This is an abstract factory that defines how the two types of components are created."""

    def __init__(self, config):
        self.config = config

    @abstractmethod
    def create_component(self, **args):
        """This creates the component based on component type"""


class TestSuiteFactory(ComponentFactory):
    """This is the concrete class to create the TestSuite component"""

    def __init__(self, config):
        super(TestSuiteFactory, self).__init__(config)

    def create_component(self, component_type):
        ts_mgr = driver.DriverManager(
            namespace="roast.component.testsuite",
            name=component_type,
            invoke_on_load=True,
            invoke_args=(self.config,),
        )
        return ts_mgr


class SystemFactory(ComponentFactory):
    """This is the concrete class to create the System component"""

    def __init__(self, config):
        super(SystemFactory, self).__init__(config)

    def create_component(self, component_types):
        system_mgr = named.NamedExtensionManager(
            namespace="roast.component.system",
            names=component_types,
            invoke_on_load=True,
            invoke_args=(self.config,),
            name_order=True,
        )
        return system_mgr


class Scenario:
    def __init__(self, config):
        self.config = config
        self.testsuite = config.get("roast.testsuite")
        self.system = config.get("roast.system")
        self._ts_mgr = None
        self._system_mgr = None

    @property
    def ts(self):
        return self._ts_mgr.driver

    def sys(self, name: str):
        return self._system_mgr._extensions_by_name[name].obj

    def load_component(self):
        if self.system is not None:
            self._system_mgr = SystemFactory(self.config).create_component(self.system)
        if self.testsuite is not None:
            self._ts_mgr = TestSuiteFactory(self.config).create_component(
                self.testsuite
            )

    def configure_component(self):
        if self.system is not None:
            self._system_mgr.map(configure_extensions, self.config)
        if self.testsuite is not None:
            self._ts_mgr.driver.configure()

    def build_component(self):
        build_result = {}
        if self.system is not None:
            build_result.update(self._system_mgr.map(build_extensions, self.config))
        if self.testsuite is not None:
            build_result[self.testsuite] = self._ts_mgr.driver.build()
        return build_result

    def deploy_component(self):
        deploy_result = {}
        deploy_result[self.testsuite] = self._ts_mgr.driver.deploy()
        return deploy_result

    def run_component(self):
        run_result = {}
        run_result[self.testsuite] = self._ts_mgr.driver.run()
        return run_result


def scenario(config):
    scn = Scenario(config)
    scn.load_component()

    return scn


def configure_extensions(ext, config):
    return (ext.name, ext.obj.configure())


def build_extensions(ext, config):
    return (ext.name, ext.obj.build())
