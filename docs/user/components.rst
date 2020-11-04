.. _component-plugins-models:

==============================
 Component Plugins and Models
==============================

While there are several different methods to load code dynamically in Python, the best approach
for ROAST is to built on top of setuptools `entry points`_. At a high level, the primary reasons
are that ROAST is a Python package and we want to avoid creating custom mechanisms. Additionally,
ROAST plugins such as the component libraries can also be packaged to extend existing ROAST
namespaces.

A plugin framework named `stevedore`_ includes the functionality needed by ROAST. Currently,
`stevedore`_ is maintained by the Redhat Openstack project, an extremely popular cloud
computing platform.

Plugin Model
============

When constructing systems, we need to establish a uniform methodology across all use cases
so that end users can focus on test development rather than system construction. This is
realized through the creation of plugin models that are defined to ensure an uniform API
across all components.

Currently, there are two plugin models implemented - `TestSuite`_ and `System`_. The abstract
interfaces are defined as ``TestSuiteBase`` (roast/component/testsuite.py) and ``SystemBase``
(roast/component/system.py).

TestSuite
---------

.. code-block:: python

    from abc import ABCMeta, abstractmethod
    
    
    class TestSuiteBase(metaclass=ABCMeta):
        """Base class for Test Suite component plugin
        """
    
        def __init__(self, config):
            self.config = config
    
        @abstractmethod
        def configure(self):
            """Abstract class method to configure the TestSuite component
            """
    
        @abstractmethod
        def build(self):
            """Abstract class method to build the TestSuite component
            """
    
        @abstractmethod
        def deploy(self):
            """Abstract class method to deploy the TestSuite component
            """
    
        @abstractmethod
        def run(self):
            """Abstract class method to run the TestSuite component
            """

This plugin model is designed for a component that will need to deploy other components and
execute an application to verify correctness. Typically, there is only one TestSuite
component for a particular test type. For example, running a validation tool to verify
correctness on a constructed system.

In this plugin model, there are four methods: :func:`configure`, :func:`build`, :func:`deploy`,
and :func:`run`. Each plugin that inherits from the base class will need to implement these
methods.

System
------

.. code-block:: python

    from abc import ABCMeta, abstractmethod
    
    
    class SystemBase(metaclass=ABCMeta):
        """Base class for System component plugins
        """
    
        def __init__(self, config):
            self.config = config
    
        @abstractmethod
        def configure(self):
            """Abstract class method to configure the System component
            """
    
        @abstractmethod
        def build(self):
            """Abstract class method to build the System component
            """

This plugin model is designed for components that make up a system. There can be one or many
system components for a particular test type. For example, an operating system and
programmable logic as part of a constructed system.

In this plugin model, there are only two methods: :func:`configure` and :func:`build`. Each plugin
that inherits from the base class will need to implement these methods.

.. seealso::

   :ref:`component-plugins`

.. _stevedore: https://github.com/openstack/stevedore
.. _entry points: https://packaging.python.org/specifications/entry-points/