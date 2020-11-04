.. _configuration-system:

==============================
 Layered Configuration System
==============================

ROAST uses a hierarchical or layered configuration system that is based on the open source 
library `python-configuration`_.

This allows for configuration to be defined through a single file with key/value pairs or 
through a hierarchical template-based approach. In the template-based approach, a master
configuration is established with interpolation expressions (placeholders) to be replaced with
the corresponding value established in another configuration file through a process called `string
interpolation`_.

Configuration files must be named **conf** and can be written in a number of format types including:

* Python (conf.py)
* YAML (conf.yaml)
* TOML (conf.toml)
* JSON (conf.json)
* INI (conf.ini)

.. seealso::

   :ref:`hello-world` tutorial for examples of project structures.

Single File
===========

In the single file approach, configuration can be defined through a file (**conf.py**).

.. code-block:: python

   var = "my_string"

Template-Based (Heirarchical)
=============================

In the template-based approach, a variable can be defined with its value to be substituted 
with another variable's value. The top-level configuation file (**conf.py**):

.. code-block:: python

   var = {string_var}

At the test specific level, the variable and its value can be defined for a specific test 
or category of tests. The test specific configuration file (**specific/conf.py**):

.. code-block:: python

   string_var = "my_string"

When both files are loaded in the library, the test specific configuration file is "layered" 
on top of the template. The Python functionality behind this is `str.format`_.

.. warning::
   For Python configuration files, string interpolation is only supported in iterables.

Dot-Based Variables
===================

Dot-based variables can be created from configuration files.

Python
------

A separator of ``__`` is used to represent a ``.``. For example:

.. code-block:: python

   aa__bb__cc = 1

would result in the configuration

.. code-block:: python

   {
       'aa.bb.c': 1,
   }

An alternative is to use ``python-box``. For example:

.. code-block:: python

   from box import Box
   aa = Box(default_box=True)
   aa.bb.cc = 1

   del Box

.. note::
   If this method is used, the last statement of ``del Box`` should be included. Otherwise, a
   key/value pair of "Box" and a ``Box`` class object will appear in the configuration.

.. warning::
   String interpolation is only supported in iterables and not dictionaries.

Other Formats
-------------

With other formats, if heirarchy is part of the specification, dot-based variables will
be created. For example, a TOML configuration:

.. code-block:: toml

   [section]
   var = "mystring"

would result in the configuration

.. code-block:: python

   {
       'section.var': 'mystring'
   }
   
Accessing Configuration Values
==============================

When creating a configuration, the ``ConfigurationSet`` object that is returned can be accessed
like a dictionary. If the configuration is assigned to ``conf``, the value of ``var`` can be
obtained using:

.. code-block:: python

   conf.get("var")
   conf["var"]
   conf.var

Similarly, dot-based variable values can be obtained using:

.. code-block:: python

   conf.get("section.var")
   conf["section.var"]
   conf.section.var

.. _python-configuration: https://github.com/tr11/python-configuration
.. _string interpolation: https://en.wikipedia.org/wiki/String_interpolation
.. _str.format: https://docs.python.org/3.6/library/string.html#format-string-syntax
