#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import logging
from roast.xexpect import Xexpect
from roast.confParser import generate_conf
from roast.component.basebuild import Basebuild
from roast.utils import *  # pylint: disable=unused-wildcard-import

log = logging.getLogger(__name__)


class Cmake(Xexpect):
    def __init__(self, config, log):
        super(Cmake, self).__init__(log)
        self.config = config
        self._configure()
        self._create_mini_sysroot()

    def _configure(self):
        self.runcmd(f"source {self.config['VITIS_SETTINGS_SH']}")

    def generate_toolchain_cmake(self, include_dirs, lib_dirs, fname="toolchain.cmake"):
        f = open(fname, "w")
        f.write(
            f"""
set( CMAKE_SYSTEM_NAME Linux )                                                 
set( CMAKE_SYSTEM_PROCESSOR aarch64 )                                          
set( CMAKE_C_COMPILER aarch64-linux-gnu-gcc )                                  
set( CMAKE_CXX_COMPILER aarch64-linux-g++ )                                     
set( CMAKE_ASM_COMPILER aarch64-linux-gnu-gcc )                                
set( CMAKE_AR aarch64-linux-gnu-ar CACHE FILEPATH "Archiver" )
set( HUGETLBFS_LIBRARY "{lib_dirs[0]}/libhugetlbfs.so" )
set( HUGETLBFS_INCLUDE_DIR "{include_dirs[0]}" )
set( LIBSYSFS_LIBRARY "{lib_dirs[0]}/libsysfs.so" )
set( LIBSYSFS_INCLUDE_DIR "{include_dirs[0]}" )
set( LIBMETAL_LIB "{lib_dirs[0]}" )
set( LIBMETAL_INCLUDE_DIR "{include_dirs[0]}" )
"""
        )

        # Set Cflags
        cflags = f"set( {self.config['cmake_flags']}"
        cflags += self.prepend(include_dirs, "-I")
        cflags += self.prepend(lib_dirs, "-L")
        cflags += '"'
        cflags += ' CACHE STRING "CFLAGS" )\n'
        f.write(cflags)
        f.close()

    def cmake_configure(self, app_name, fname="toolchain.cmake", extra_args=""):
        self.build_dir = f"{self.config['workDir']}/{app_name}/build"
        self.runcmd(f"cd {self.build_dir}")
        self.runcmd(
            f"cmake .. -DCMAKE_TOOLCHAIN_FILE=../../{fname} {extra_args}",
            expected_failures="No such file or directory",
        )

    def cmake_compile(self):
        self.runcmd(f"cd {self.build_dir}")
        self.runcmd(
            "VERBOSE=1 cmake --build ./ --target all -- -j 20",
            expected_failures="No such file or directory",
        )

    def prepend(self, lst, val):
        ret = ""
        for e in lst:
            ret += f" {val}{e}"

        return ret

    def _create_mini_sysroot(self):
        self.mini_sysroot_dir = f"{self.config['workDir']}/mini_sysroot"
        mkdir(self.mini_sysroot_dir)
        self.runcmd(f"cd {self.mini_sysroot_dir}")
        for rpm in get_files(self.config["rpm_dir"], "rpm"):
            self.runcmd(f"rpm2cpio {self.config['rpm_dir']}{rpm} | cpio -idmv")
        self.mini_sysroot_include = f"{self.mini_sysroot_dir}/usr/include"
        self.mini_sysroot_lib = f"{self.mini_sysroot_dir}/usr/lib"
        mkdir(f"{self.mini_sysroot_dir}/lib")
        copyDirectory(f"{self.mini_sysroot_dir}/lib", f"{self.mini_sysroot_lib}")


def build_libmetal(cmkobj):
    clone(
        cmkobj.config.git.libmetal,
        f"{cmkobj.config['workDir']}/libmetal",
        "libmetal.log",
        cmkobj.config["workDir"],
    )
    mkdir(f"{cmkobj.config['workDir']}/libmetal/build")
    cmkobj.cmake_configure(app_name="libmetal")
    cmkobj.cmake_compile()
    copyDirectory(f"{cmkobj.build_dir}/lib/include", f"{cmkobj.mini_sysroot_include}")
    copyDirectory(f"{cmkobj.build_dir}/lib/", f"{cmkobj.mini_sysroot_lib}")


def build_openamp(cmkobj):
    clone(
        cmkobj.config.git.openamp,
        f"{cmkobj.config['workDir']}/open-amp",
        "openamp.log",
        cmkobj.config["workDir"],
    )
    mkdir(f"{cmkobj.config['workDir']}/open-amp/build")
    cmkobj.cmake_configure(app_name="open-amp")
    cmkobj.cmake_compile()
    copyDirectory(
        f"{cmkobj.config['workDir']}/open-amp/lib/include",
        f"{cmkobj.mini_sysroot_include}",
    )
    copyDirectory(f"{cmkobj.build_dir}/lib/", f"{cmkobj.mini_sysroot_lib}")


def build_aie_lib(cmkobj, component):
    cmd_list = [
        f'export CC="aarch64-linux-gnu-gcc\
 -I{cmkobj.mini_sysroot_include} -L{cmkobj.mini_sysroot_lib}"',
        f"cd {cmkobj.config['workDir']}",
    ]
    cmkobj.runcmd_list(cmd_list)
    if component == "embeddedsw":
        aie_lib_src = "XilinxProcessorIPLib/drivers/aiengine/src"
    elif component == "eswv2":
        component = "embeddedsw"
        aie_lib_src = "XilinxProcessorIPLib/drivers/aienginev2/src"
    else:
        component = "aienginev2"
        aie_lib_src = "src"

    if cmkobj.config[f"external_{component}"]:
        aie_lib_src = os.path.join(cmkobj.config[f"external_{component}"], aie_lib_src)
    else:
        aie_lib_src = os.path.join(cmkobj.config["workDir"], component, aie_lib_src)
        clone(
            cmkobj.config.git[f"{component}"],
            os.path.join(cmkobj.config["workDir"], component),
            "build_aie_lib.log",
            cmkobj.config["workDir"],
        )

    cmd = f"make CFLAGS='-D__AIELINUX__ -Wall' -C {aie_lib_src} -f Makefile.Linux"
    cmkobj.config["aie_lib_path"] = aie_lib_src
    cmkobj.runcmd(cmd, expected_failures="Error")


def aie_linux_lib_builder(config):
    ret = False
    bc = Basebuild(config)
    cm = Cmake(config, log)
    cm.generate_toolchain_cmake(
        include_dirs=[cm.mini_sysroot_include], lib_dirs=[cm.mini_sysroot_lib]
    )

    # Build Libmetal Linux Library
    build_libmetal(cm)
    # Build Openamp linux Library
    build_openamp(cm)
    # Build AIE Linux Library
    build_aie_lib(cm, config.linux_lib_component)
    ai_engine_src_path = f"{cm.config['aie_lib_path']}/"
    files = get_files(ai_engine_src_path, filename="libxaiengine", abs_path=True)
    # Deploy generated lib files
    for lib in files:
        copy_file(lib, f"{config['imagesDir']}")
        cmd_list = [
            f"cd {config['imagesDir']}",
            f"tar cvfj {config['test']}.tar.xz ./libxaiengine.*",
        ]
        cm.runcmd_list(cmd_list)
        ret = True
    return ret
