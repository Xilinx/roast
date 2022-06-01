=====================================================
 ROAST -- Randomized Okaying Across System Topologies
=====================================================

.. meta::
   :description lang=en: An open-source Python framework that simplifies the development of complex validation test suites.

ROAST is an open-source Python framework that simplifies the development of complex validation
test suites. To accomplish this, ROAST provides a collection of interfaces that allows test
developers to build test suites in a highly structured manner.

Key features:

- Compose systems from Xilinx or custom components
- Define systems composed from various configuration sources
- Heirarchical configuration system
- Randomized data provider for randomized testing
- Generic APIs for simplified usage and access
- Plugin system for extensibility

To find out more, visit :doc:`/features`.

First steps
-----------

New to test development? Learn how to establish a Python environment and a test repository
for your testing requirements.

* **Installation**: :doc:`/intro/install`

* **Getting started**: :ref:`intro/getting_started:environment setup` | :ref:`intro/getting_started:repository structure`

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Getting Started

   intro/install
   intro/getting_started
   features

ROAST feature overview
----------------------

* **Scaling test suites through configuration**:
  :doc:`configuration` |
  :doc:`complex_structures`

* **Test execution with pytest**:
  :doc:`pytest_fixtures`

* **Randomization**:
  :doc:`provider`

.. toctree::
   :maxdepth: 3
   :hidden:
   :caption: Feature Overview

   configuration
   complex_structures
   pytest_fixtures
   provider

ROAST examples
--------------

* **Complete examples**:
  :doc:`examples_repository`

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Example

   examples_repository

Advanced features of ROAST
--------------------------

* **Developer Interface**:
  :doc:`reference/index`

* **Building plugins**:
  :doc:`advanced/component_models` |
  :doc:`advanced/component_plugins`

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Advanced features

   reference/index
   advanced/component_models
   advanced/component_plugins

.. Indices and tables
.. ==================

.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`
