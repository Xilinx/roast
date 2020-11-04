.. _pytest-fixture-usage:

================
 Pytest Fixture
================

.. contents::
  :local:

Parameterize with machine option
================================

Is this example, predefined values based on the machine type are used. The files that hold these
values exist in the **roast/machines** directory.

zynq.py snippet

.. code-block:: python

    platform = "zynq"

versal.py snippet

.. code-block:: python

    platform = "versal"

test_fixture.py

.. code-block:: python

    import pytest

    @pytest.fixture
    def get_machine(request, get_cmdl_machine_opt):
        return get_cmdl_machine_opt[request.param]

    @pytest.mark.parametrize("get_machine", range(2), indirect=True)
    def test_something(request, create_configuration, get_machine):
        config = create_configuration(machine=get_machine)
        assert config.platform == get_machine

This is called with::

  $ pytest --machine=zynq,versal

In this example, ``test_something`` is being parameterized with two ``machine`` values **zynq**
and **versal** that are specified by the command line option ``--machine``. When decorating the
test with ``@pytest.mark.parametrize`` with the ``indirect`` parameter set to ``True``, the
fixture named as the first parameter will be called. When the fixture ``get_machine`` is called,
it will in turn call the ``get_cmdl_machine_opt`` fixture. This will return the values set with
the command line option ``--machine`` and also return the indexed value set by ``request.param``.

The second parameter will be iterated over with its value will be written to ``request.param``.
In this case, the values of 0 and 1 will be written with each iteration.

For each iteration of the test, the value of ``get_machine`` will be **zynq** and **versal**.

Now let's run the test with the **-v** option to see the full results::

    $ pytest -v --machine=zynq,versal
    =================== test session starts ==================
    ..
    collected 2 items

    tests/test_fixtures.py::test_something[0] PASSED    [ 50%]
    tests/test_fixtures.py::test_something[1] PASSED    [100%]

    ==================== 2 passed in 0.04s ===================