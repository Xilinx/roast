.. _component-plugins:

===================
 Component Plugins
===================

In this tutorial, we will discuss how to create and load component plugins. If you're not familiar
with the component models, please first visit :ref:`component-plugins-models` for details.

Creating Plugins
================

Steps to creating a component plugin:

1. With the two possible plugin models, ``TestSuiteBase`` or ``SystemBase``, choose the model that
   fits for your component plugin.
2. Subclass the base class and implement the required methods.
3. Define the name of the plugin and extend one of two possible roast component namespaces.

Let's start with a system component named ``MySystem`` that has two methods, :func:`configure`
and :func:`build`. This will be created in **my_system.py**.

Create a test suite component named ``MyTestSuite`` that has four methods, :func:`configure`,
:func:`build`, :func:`deploy`, and :func:`run`. This will be create in **my_testsuite.py**.

We will need a configuration file named **conf.py** to define which components will be used in
the test scenario and a test module named **test_scenario.py**. Add these into the **tests** directory::

   repository/
   └── tests/
       ├── conf.py
       ├── my_system.py
       ├── my_testsuite.py
       └── test_scenario.py

conf.py

.. code-block:: python

    roast = {"system": ["my_system"], "testsuite": "my_testsuite"}
    var = "hello world"

Here, we define a system component named ``"my_system"`` and a testsuite component named
``"my_testsuite"``.

.. note::
   These names are identifiers used by each plugin when registering as an entry point and do not
   need to match the module filename.

   Also note that the value for ``system`` is a list since a test scenario could have more than
   one.

my_system.py

.. code-block:: python

    from roast.component.system import SystemBase

    class MySystem(SystemBase):
        def __init__(self, config):
            super().__init__(config)

        def configure(self):
            print("MySystem configure called")

        def build(self):
            msg = "MySystem build called"
            print(msg)
            return msg

        def custom_method(self, data):
            msg = f"MySystem custom method called with {data}"
            print(msg)
            return msg

Here, we are subclassing from the ``SystemBase`` abstract base class and implementing the required
methods :func:`configure` and :func:`build`. In addition, we are going to extend the class with
a method named :func:`custom_method`.

The :func:`super` call in :func:`__init__` is where the configuration is stored as an
attribute of the class and can accessed through ``self.config``.

my_testsuite.py

.. code-block:: python

    from roast.component.testsuite import TestSuiteBase

    class MyTestSuite(TestSuiteBase):
        def __init__(self, config):
            super().__init__(config)

        def configure(self):
            print("MyTestSuite configure called")

        def build(self):
            msg = "MyTestSuite build called"
            print(msg)
            return msg

        def deploy(self):
            print("MyTestSuite deploy called")

        def run(self):
            msg = "MyTestSuite run called"
            print(msg)
            return msg

        def custom_method(self, data):
            msg = f"MyTestSuite custom method called with {data}"
            print(msg)
            return msg

Similar to ``MySystem``, subclass and implement the required methods. Also extend the class with
a custom method.

Loading Plugins
===============

In order to dynamically load component plugins, they first need to be registered in the ROAST
namespace as an object that can be called through entry points. Two namespaces are available:
``roast.component.testsuite`` for a TestSuite component and ``roast.component.system`` for System
components.

test_scenario.py

.. code-block:: python

    import inspect
    from roast.utils import register_plugin
    import my_system, my_testsuite

    def test_my_scenario(create_scenario):
        system_name = "my_system"
        system_location = inspect.getsourcefile(my_system)
        register_plugin(
            system_location, system_name, "system", "my_system:MySystem",
        )
        testsuite_name = "my_testsuite"
        testsuite_location = inspect.getsourcefile(my_testsuite)
        register_plugin(
            testsuite_location, testsuite_name, "testsuite", "my_testsuite:MyTestSuite",
        )

        scn = create_scenario()
        my_ts = scn.ts
        my_sys = scn.sys(system_name)

        scn.configure_component()
        assert my_ts.config.var == "hello world"
        assert my_sys.config.var == "hello world"

        build_results = scn.build_component()
        assert build_results[testsuite_name] == "MyTestSuite build called"
        assert build_results[system_name] == "MySystem build called"

        scn.deploy_component()

        run_results = scn.run_component()
        assert run_results[testsuite_name] == "MyTestSuite run called"

        custom_result = my_ts.custom_method(data="hello")
        assert custom_result == "MyTestSuite custom method called with hello"
        custom_result = my_sys.custom_method(data="hello")
        assert custom_result == "MySystem custom method called with hello"

Here, we need to first register the ``MySystem`` and ``MyTestSuite`` classes. In order to register,
we will need their file locations which can be hard coded or obtained through the use of
:func:`inspect.getfile`.

If the component objects will be packaged into a Python package, this can be defined in
**setup.py**.

.. code-block:: python

    entry_points={
        "roast.component.system": ["repository.tests.my_system = my_system:MySystem",],
        "roast.component.testsuite": ["repository.test.my_testsuite = my_testsuite:MyTestSuite",],
    }

Next, we call the :func:`create_scenario` fixture to load the components and also generate a
configuration. The variable ``scn`` holds references to both ``MySystem`` and ``MyTestSuite``
instances. To access the specific instance, use ``scn.ts`` for test suite or ``scn.sys``
for systems. For systems, the specific name is required since there can be more than one system
component. Here, we're going to assign the instances to ``my_ts`` and ``my_sys``.

Calling the :func:`configure_component` method will in turn call the :func:`configure` method
in every loaded instance. In both ``MySystem`` and ``MyTestSuite``, the configuration is stored as
a ``config`` attribute. With ``my_ts.config.var``, we can access the value of ``var`` in the
``MyTestSuite`` instance and similarly with ``my_sys.config.var`` for ``MySystem``. Both should
return ``"hello world"``.

Similarly, when :func:`build_component` is called, this will call :func:`build` in each
instance. The difference here is that values are returned in a dictionary that can be accessed
using the name as the key.

The methods :func:`deploy_component` and :func:`run_component` are essentially the same as
the previous two except that these call **only** the ``MyTestSuite`` instance since systems do not
have :func:`deploy` or :func:`run` methods.

Lastly, since we access to the instances, we can call custom methods, pass parameters, and also
return values.

Let's now execute the tests::

    $ pytest -rP
    =========== test session starts ===========
    ..
    collected 1 item

    tests/test_scenario .                [100%]

    ===========================================
    ---------- Captured stdout call -----------
    MySystem configure called
    MyTestSuite configure called
    MySystem build called
    MyTestSuite build called
    MyTestSuite deploy called
    MyTestSuite run called
    MyTestSuite custom method called with hello
    MySystem custom method called with hello
    ============ 1 passed in 0.12s ============