.. _hello-world:

=============
 Hello World
=============

The objective of this tutorial is to build a test repository starting with a a basic test and
expanding to more complex parameterized and categoried tests leveraging ROAST to generate its
configuration.

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

Tests can be structured in a number of ways. In this tutorial, we'll first start with a basic
structure and then expand to parameterized and categorized tests.

Basic
-----

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

In **test_basic.py**, we can see that the ``create_configuration`` fixture is called which reads
from **conf.py** and assigns it to the ``conf`` variable. The value of ``var`` is then accessed
by accessing ``conf.var``.

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

Parameterized
-------------

Now we're going to parameterize the test. Create with the following structure and files::

   parameterized/
   └── tests/
       ├── parameter1/
       |   └── conf.py
       ├── parameter2/
       |   └── conf.py
       ├── test_parameterized.py
       └── conf.py

conf.py

.. code-block:: python

    var = "{hello_world}"

Here, we are defining a variable ``var`` with an interpolation expression expecting another
variable named ``hello_world`` to replace its value.

parameter1/conf.py

.. code-block:: python

    hello_world = "hello parameter 1"

When this configuration file is layered onto the first, the value of both ``hello_world`` and
``var`` is ``"hello parameter 1"``.

parameter2/conf.py

.. code-block:: python

    hello_world = "hello parameter 2"

The value of ``hello_world`` and ``var`` is ``"hello parameter 2"``.

test_parameterized.py

.. code-block:: python

    import pytest
    from collections import namedtuple

    Properties = namedtuple("Properties", ["parameter", "expected"])

    def get_test_properties():
        p1 = Properties("parameter1", "hello parameter 1")
        p2 = Properties("parameter2", "hello parameter 2")
        return [p1, p2]

    @pytest.mark.parametrize("properties", get_test_properties())
    def test_parameterized(properties, create_configuration):
        conf = create_configuration(test_name="", params=[properties.parameter])
        assert conf.var == properties.expected

In **test_parameterized.py**, we have defined a test named :func:`test_parameterized`. The
``@pytest.mark.parametrize`` decorator defines that the value of the ``properties`` variable will
have its value determined by the output of the :func:`get_test_properties` function for each
iteration of the test. When this is passed into the ``params`` parameter of the
``create_configuration`` pytest fixture as a list, the additional configuration files from the
``params`` directory are retrieved for that iteration.

.. note::
   The ``params`` parameter is a list to allow additional depths of directories. For this
   tutorial, we have a depth of 1.

The ``test_name`` parameter is set to empty string ``""``. The `Categorized`_ section will
describe this in further detail.

For the first iteration, ``properties.parameter`` will have a value of ``"parameter1"``. The
``params`` parameter will have a value of ``["parameter1"]``. This will cause the
``create_configuration`` fixture to search for configuration files in **tests** and
**tests/parameter1** directories. The ``properties.expected`` value that is compared with
``config.var`` is ``"hello parameter1"``.

For the second iteration, ``properties.parameter`` has a value of ``"parameter2"``. The ``params``
parameter has a value of ``["parameter2"]`` and the configuration files from directories **tests**
and **test/parameter2** will be used. The ``properties.expected`` value that is compared with
``config.var`` is ``"hello parameter2"``.

.. note::
   For more details on test parameterization, visit `pytest parameterization`_.

Let's see what pytest collects as tests::

    $ pytest --collect-only
    =========== test session starts ===========
    ..
    collected 2 items
    <Module tests/test_parameterized.py>
      <Function test_parameterized[properties0]>
      <Function test_parameterized[properties1]>

    ========= no tests ran in 0.02s ===========

In the output, the number of iterations and the parameters of each are shown.

We can now execute the tests::

    $ pytest
    ======== test session starts =========
    ..
    collected 2 items

    tests/test_parameterized.py ..  [100%]

    ========= 2 passed in 0.06s ==========

If we only wanted to execution one particular iteration::

    $ pytest -k test_parameterized[properties0]
    =============== test session starts ================
    ..
    collected 2 items / 1 deselected / 1 selected

    tests/test_parameterized.py .                 [100%]

    ========= 1 passed, 1 deselected in 0.010 ==========

Categorized
-----------

In this next section, we're going to increase the complexity with additional tests in another
module. Create the following structure and files::

   categorized/
   └── tests/
       ├── category
       |   ├── something
       |   │   ├── parameter1
       |   │   │   └── conf.py
       |   │   └── parameter2
       |   │       └── conf.py
       |   ├── something_else
       |   │   ├── parameter1
       |   │   │   └── conf.py
       |   │   └── parameter2
       |   │       └── conf.py
       |   ├── test_something_else.py
       |   └── test_something.py
       └── conf.py

conf.py

.. code-block:: python

    var = "{hello_world}"

something/parameter1/conf.py

.. code-block:: python

    hello_world = "hello parameter 1"

something/parameter2/conf.py

.. code-block:: python

    hello_world = "hello parameter 2"

something_else/parameter1/conf.py

.. code-block:: python

    hello_world = "hello parameter 3"

something_else/parameter2/conf.py

.. code-block:: python

    hello_world = "hello parameter 4"

test_something.py

.. code-block:: python

    import pytest
    from collections import namedtuple

    Properties = namedtuple("Properties", ["parameter", "expected"])

    def get_test_properties():
        p1 = Properties("parameter1", "hello world 1")
        p2 = Properties("parameter2", "hello world 2")
        return [p1, p2]

    @pytest.mark.parametrize("properties", get_test_properties())
    def test_something(properties, create_configuration):
        conf = create_configuration(params=[properties.parameter])
        assert conf.var == properties.expected

test_something_else.py

.. code-block:: python

    import pytest
    from collections import namedtuple

    Properties = namedtuple("Properties", ["parameter", "expected"])

    def get_test_properties():
        p1 = Properties("parameter1", "hello world 3")
        p2 = Properties("parameter2", "hello world 4")
        return [p1, p2]

    @pytest.mark.parametrize("properties", get_test_properties())
    def test_something_else(properties, create_configuration):
        conf = create_configuration(params=[properties.parameter])
        assert conf.var == properties.expected

Notice that in the ``create_configuration`` call of both modules, the ``test_name`` parameter is
not specified. When not specified, the value internally is taken from the node name. The
``"test_"`` prefix is removed along with the characters after ``[``.

For example, if we execute::

    $ pytest -k test_something[properties0]

The variable ``test_name`` will be ``"something"``. If we execute::

    $ pytest -k test_something_else[properties0]

The variable ``test_name`` will be ``"something_else"``.

In both cases, the ``test_name`` directory will be an additional directory that is searched for
configuration files.

The order of search directories is **top level**, **category**, **test name**, and **parameter**.

For the test case of **test_something[properties0]**, the order of directories searched is:
**tests** (top level), **category** (directory of test modules), **something** (based on
``test_name``), and **parameter1** (based on ``params``).

Let's now execute the tests::

    $ pytest
    ========== test session starts ==========
    ..
    collected 4 items

    category/test_something.py ..      [ 50%]
    category/test_something_else.py .. [100%]

    =========== 4 passed in 0.21s ===========

.. _pytest: https://pytest.org/
.. _virtual environment: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/
.. _pytest parameterization: https://docs.pytest.org/en/stable/parametrize.html