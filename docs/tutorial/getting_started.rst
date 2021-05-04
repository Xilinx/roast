.. _getting-started:

=================
 Getting Started
=================

The objective of this tutorial is to build a test repository starting with a a basic test
leveraging ROAST to generate its configuration.

.. contents::
  :local:

Environment Setup
=================

While ROAST is test runner agnostic, this tutorial will use `pytest`_ and
:ref:`pytest fixtures<pytest-fixtures>` developed specifically for ROAST. This means both ``roast``
and ``pytest-roast`` packages must be installed. While optional, it is highly recommended that
these are installed into a `virtual environment`_.

Upon installation of ``pytest-roast``, ``pytest`` will automatically be installed as a dependency.

.. note::
   Please review :ref:`installation` instructions on how to install Python packages using pip.

Repository Structure
====================

Tests can be structured in a number of ways. In this tutorial, we'll start with a basic structure.

Create a repository with the following structure and files::

   basic/
   └── tests/
       ├── test_basic.py
       └── conf.py

conf.py

.. code-block:: python

    var = "hello world"

test_basic.py

.. code-block:: python

    import pytest

    def test_basic(create_configuration):
        conf = create_configuration()
        assert conf.var == "hello world"

In **test_basic.py**, when ``pytest`` is imported, all pytest fixtures will be available. Since
``pytest-roast`` is installed as a pytest plugin, the ``create_configuration`` fixture is
also available and can be added as an argument to the test. When called, the configuration is read
from **conf.py** and assigned to the ``conf`` variable. The value of ``var`` is then accessed by
accessing ``conf.var``.

.. note::
   For other methods of accessing configuration values, visit :ref:`configuration-system`.

First, let's see what pytest collects as tests::

    $ pytest --collect-only
    ======= test session starts ========
    ..
    collected 1 item
    <Module tests/test_basic.py>
      <Function test_basic>

    ====== no tests ran in 0.04s =======

We can now execute the test::

    $ pytest
    ====== test session starts =======
    ..
    collected 1 item

    tests/test_basic.py .       [100%]

    ======= 1 passed in 0.18s ========

.. note::
   Visit :ref:`complex-repository-structures` for advanced parameterized and categorized testing
   scenarios.

.. _pytest: https://pytest.org/
.. _virtual environment: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/
.. _pytest parameterization: https://docs.pytest.org/en/stable/parametrize.html