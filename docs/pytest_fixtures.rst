=============================
 Pytest Fixtures and Options
=============================

While the ROAST test framework is test-tool agnostic, pytest fixtures have been provided to
simplify test creation and execution. The fixtures provided are grouped into three categories.

.. contents::
  :local:

Configuration Generation
========================

The features in this section provide functionality related to generating a test configuration.

create_configuration fixture
----------------------------

This fixture will generate a configuration based on the location of the test file being executed.
The optional parameters to this fixture are:

* ``test_name`` - This specifies a test configuration to be retrieved in a subdirectory
  relative to the test file. If not provided, this will resolve to ``request.node.name``.
* ``base_params`` - The list provided is written to the base_params attribute of the
  configuration.
* ``params`` - This allows a list of test configurations to be retrieved in subdirectories
  relative to the test file. This is typically used to retrieved definitions when parameterizing
  tests.
* ``overrides`` - This allows variable overrides to be specified. This can be another Python file,
  key/value pair, or both. If not provided, it will attempt to use ``pytest.override`` from the
  :ref:`override-option`.
* ``machine`` - This specifies an override file based on the machine type where the test will be
  executed. If not provided, it will attempt to use ``pytest.machine`` from the
  :ref:`machine-option`.

.. seealso::

   :func:`roast.confParser.generate_conf`

.. _override-option:

\-\-override option
-------------------

This option allows the user to specify an override file, key/value pairs, or both to override
variable values in the configuration generated from configuration files.

Examples:

To override a variable named "my_version"::

  $ pytest --override my_version=2020.1

To override a list variable named "my_list"::

  $ pytest --override my_list=c,d

To override multiple variables defined in a Python file::

  $ pytest --override /path/to/file.py

To override using both file and key/value pair::

  $ pytest --override /path/to/file.py my_version=2020.1

.. _machine-option:

\-\-machine option
------------------

This option allows the user to specific an override file from a specific location. The
functionality is the same as using an override by file except that the file location does not
need to be specified.

To override using a machine file::

  $ pytest --machine zynq

\-\-randomize option
--------------------

This option allows the user to set a global `randomize` configuration parameter to `True` or
`False`. If not specified, this is set to `False` by default.

To enable randomization::

  $ pytest --randomize

Board Acquisition
=================

The fixtures in this section provide wrappers for easy board acquisition.

board_session fixtures
----------------------

These fixtures will return an instantiated ``Board`` object based on the ``board_type`` keyword
argument. For example, the ``host_board_session`` fixture will instantiate a ``Board`` object with
``board_type="host_target"`` and return a ``TargetBoard`` object.

This is accomplished through loading of the ``TargetBoard`` object as an entry point upon
installation of the ``roast-xilinx`` package. Custom ``Board`` classes can be written and
registered as a plugin where additional fixtures can be created to call the custom classes.

board fixture
-------------

This fixture wraps `board_session fixtures`_ and attempts to retrieve the ``board_interface`` key
from the configuration to be used as the ``board_type``. A valid board type must be specified
otherwise an exception will be generated.

Upon return, the ``Board`` object will have attributes such as:

* config
* target_console - console session with a board

Additionally, the :func:`start` method will be called to initialized the board.

Scenario Generation
===================

The fixture is an all-in-one wrapper for configuration generation and automated loading of test
suites and system components of a test system.

create_scenario fixture
-----------------------

This fixture wraps the `create_configuration fixture`_ and calls :func:`roast.component.scenario`
to return a ``Scenario`` object which contains handles to all loaded plugins (instantiated
classes).