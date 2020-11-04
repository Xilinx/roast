.. _scenario-class:

Scenario class
==============

A ``Scenario`` class in **component/_init_.py** is provided within ROAST which will create and
save references to component plugins. This class has high level methods to dispatch method
calls to the loaded components. These include:

* ``load_component`` - calls the **__init__.py** component class constructor
* ``configure_component`` - calls the :func:`configure()` component method
* ``build_component`` - calls the :func:`build()` component method and returns result
* ``deploy_component`` (TestSuite only) - calls the :func:`deploy()` component method and returns
  result
* ``run_component`` (TestSuite only) - calls the :func:`run()` component method and returns result

Accessor methods are also available to access the direct component object themselves. These
include:

* :func:`ts()` - returns the object of the TestSuite component
* :func:`sys()` - returns the object of the System component specified by component name (because
  there can be more than one system component)