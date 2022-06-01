=====================
 Examples Repository
=====================

In this repository, full working examples are available to showcase various features of ROAST. 
These range from simple "hello word" applications to full Linux images.

Varying styles of repository structures and test parameterization are provided to illustrate
how test variants can be defined within a test suite.

To download these examples, visit https://github.com/Xilinx/roast-examples.

Prerequisites
=============

User needs to install Python3 version >=3.6 along with pip3 and virtual environments python package. 

- Python3.6 +
- pip3
- virtualenv 
- picocom  (Terminal emulator for serial port access and communication)
- xvfb

The PetaLinux tools need to be installed as a non-root user.

This repo has been tested with below version along with dependent Xilinx tools/packages/libraries on Ubuntu 18.04 machine as mentioned below:

- roast 2.1.0
- pytest-roast 1.2.0.post1
- roast-xilinx 2.1.0
- Petalinux 2020.2
- Vitis 2020.2

Addtional documentation:

- `Xilinx PetaLinux installation user guide`_
- `Xilinx Vitis installation user guide`_                                                                                                                          
- `Common issues user guide`_

In ROAST, picocom application has been used for connecting and disconnecting local board support.
https://github.com/npat-efault/picocom

Tests need to be executed with a bash prompt shown in the format:

.. code-block:: bash

    bash-4.2$

Fetch the repository roast-examples tests repo:

.. code-block:: bash

    # Cloning roast-examples regression to be tested
    $ git clone https://github.com/Xilinx/roast-examples.git

    # Go to roast-examples directory
    $ cd roast-examples

Hello World
===========

Executing build test cases from hello_world directory:

.. code-block:: bash

    $ pytest hello_world/test_hello_world.py -k "build" -vv

Executing run test cases from hello_world directory:

.. code-block:: bash

    $ pytest hello_world/test_hello_world.py -k "run" -vv

PetaLinux
=========

PetaLinux prerequisites
-----------------------

Download page link where you find packages/BSPs for petalinux test cases:
https://www.xilinx.com/support/download/index.html/content/xilinx/en/downloadNav/embedded-design-tools/2020-2.html

Zynq UltraScale+ MPSoC Board Support Packages - <version>                                                                                                                     
   ---> Download:- ZCU106 BSP (BSP - 1.74 GB)

Zynq-7000 SoC Board Support Packages - <version>                                                                                                                               
   ---> Download:- ZC706 BSP (BSP - 110.74 MB)

.. note::
   Once plnx build test case is run successfully, you can use rootfs.cpio file from "build/zynqmp/<zcu106_bsp/zc706_bsp>/images/" and 
   rename osl_demo's required file. Also alternately, you can use xilinx open source base rootfs file.  

Incase if you have issue running multiple test cases, use usb_relay to auto power on and off board.

Replace <version> with your requirement. Also note that size of each file may be different depends on version.

Executing plnx_demo tests
-------------------------

Executing build test cases from plnx_demo:

.. code-block:: bash

    $ pytest plnx_demo/test_zynqmq_bsp.py -k "build" -vv

Executing run tests cases from plnx_demo:

.. code-block:: bash

    $ pytest plnx_demo/test_zynqmq_bsp.py -k "run" -vv

OSL
===

OSL prerequisites
-----------------

User has to copy respective base-rootfs files based on platform from tar/zip folder to osl_demo_basic/component/src path directory structure as mentioned below:                                     

.. code-block::

    component                                                                                                                                                    
    │   └── src                                                                                                                                                                     
    │       ├── mkimage                                                                                                                                          
    │       ├── zynq                                                                                                                                             
    │       │   └── petalinux-image-minimal-zynq-generic.rootfs.cpio                                                                                             
    │       └── zynqmp                                                                                                                                           
    │           └── petalinux-image-minimal-zynqmp-generic.rootfs.cpio                                                                                           

Examples:

- osl_demo_basic/component/src/zynqmp/petalinux-image-minimal-zynqmp-generic.rootfs.cpio
- osl_demo_basic/component/src/zynq/petalinux-image-minimal-zynq-generic.rootfs.cpio

Executing osl_demo tests
------------------------

Executing build test cases from osl_demo_basic:

.. code-block:: bash

    $ pytest osl_demo_basic/test_build_osl_basic.py -k zcu106 -vv

Executing run test cases from osl_demo_basic:

.. code-block:: bash

    $ pytest osl_demo_basic/test_run_osl_basic.py -k zcu106 -vv


Advanced OSL
============

Advanced OSL prerequisites
--------------------------

User has to create two folder namely zynqmp and zynq under component/rootfs/src path directory structure as mentioned below:                                                            
And copy respective base-rootfs files based on platform from tar/zip folder.

.. code-block:: 

    component                                                                                                                                                                           
    ├── rootfs                                                                                                                                                                        
    │   ├── conf.py                                                                                                                                                                    
    │   └── src                                                                  
    │       ├── mkimage                                                                                                                                                               
    │       ├── zynq                                                                                                                                                                   
    │       │   └── petalinux-image-minimal-zynq-generic.rootfs.cpio                                                                                                                     
    │       └── zynqmp                                                                                                                                                                   
    │           └── petalinux-image-minimal-zynqmp-generic.rootfs.cpio                                                                                                                   

Examples:

- osl_demo/component/rootfs/src/zynqmp/petalinux-image-minimal-zynqmp-generic.rootfs.cpio
- osl_demo/component/rootfs/src/zynq/petalinux-image-minimal-zynq-generic.rootfs.cpio

Executing advanced osl_demo tests
---------------------------------

Executing build test cases from osl_demo:

.. code-block:: bash

    $ pytest osl_demo/test_build_osl.py --machine=zcu106 -vv

Executing run test cases from osl_demo:

.. code-block:: bash

    $ pytest osl_demo/test_run_osl.py --machine="zcu106" -vv

.. _Xilinx PetaLinux installation user guide: https://github.com/Xilinx/roast-examples/blob/master/docs/PetaLinux_installation_user_guide.txt
.. _Xilinx Vitis installation user guide: https://github.com/Xilinx/roast-examples/blob/master/docs/Xilinx_Vitis_installation_user_guide.txt
.. _Common issues user guide: https://github.com/Xilinx/roast-examples/blob/master/docs/Common_issues_user_guide.txt
