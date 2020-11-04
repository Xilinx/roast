.. _pytest-fixtures:

=============================
 Pytest Fixtures and Options
=============================

While the ROAST test framework is test-tool agnostic, pytest fixtures have been provided to
simplify test creation and execution. The fixtures provided are grouped into three categories.

.. contents::
  :local:

Please review :ref:`pytest-fixture-usage` for usage examples.

Configuration Generation
========================

The features in this section provide functionality related to generating a test configuration.

create_configuration
--------------------

This fixture will generate a configuration based on the location of the test file being executed.
The optional parameters to this fixture are:

* ``test_name`` - This specifies a test configuration to be retrieved in a subdirectory
  relative to the test file. If not provided, this will resolve to ``request.node.name``.
* ``base_params`` - The list provided is written to the base_params attribute of the
  configuration.
* ``params`` - This allows a list of test configurations to be retrieved in subdirectories
  relative to the test file. This is typically used to retrieved definitions when parameterizing
  tests.
* ``machine`` - This specifies an override file based on the machine type where the test will be
  executed.

.. seealso::

   :func:`roast.confParser.generate_conf`

get_cmdl_machine_opt
--------------------

This fixture retrieves the values used when pytest is invoked with the command line option
``--machine``.

Example::

  $ pytest --machine=versal,zynq

\-\-override option
-------------------

This option when invoking pytest allows the user to specify an override file or key/value pairs
to overwrite the configuration generated from files.

Examples:

To override a variable named "my_version"::

  $ pytest --override="my_version=2020.1"

To override a list variable named "my_list"::

  $ pytest --override="my_list=c,d"

Board Acquisition
=================

The fixtures in this section provide wrappers for easy board acquisition.

board_session
-------------

This fixture will return an instantiated ``Board`` object based on the ``board_type`` keyword
argument. By default, ``board_type="target"`` and will return a ``TargetBoard`` object. However,
a custom ``Board`` class can be written and registered as a new type to be called through this
fixture.

get_board
---------

This fixture wraps `board_session`_ and attempts to retrieve the ``board_interface`` key
from the configuration to be used as the ``board_type``. If not found,
``board_type="target"`` is used.

Upon return, the ``Board`` object will have attributes such as:

* config
* target_console - console session with a board

Additionally, the :func:`start` method will be called to initialized the board.

Scenario Generation
===================

The `create_scenario`_ fixture is an all-in-one wrapper for configuration generation and
automated loading of test suites and system components of a test system.

create_scenario
---------------

This fixture wraps `create_configuration`_ and calls :func:`roast.component.scenario` to return
a ``Scenario`` object which contains handles to all loaded plugins (instantiated classes).