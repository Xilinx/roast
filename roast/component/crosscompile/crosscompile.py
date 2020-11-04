#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import time
import logging
from roast.xexpect import Xexpect
from roast.component.basebuild import Basebuild
from roast.utils import *  # pylint: disable=unused-wildcard-import

log = logging.getLogger(__name__)


class CrossCompile(Basebuild):
    def __init__(self, config, app_name, setup=True):

        super(CrossCompile, self).__init__(config, setup=setup)
        if has_key(config, "console"):
            self.console = config.console
        else:
            self.console = Xexpect(log, exit_nzero_ret=True)
            setattr(config, "console", self.console)

        self._copy_src()
        self.srcDir = os.path.join(self.config["workDir"], "src")
        self.app_name = app_name
        self._setup_args()
        self._configure()

    def _copy_src(self):
        src = (
            f"{self.config['ROOT']}/"
            + "/".join(self.config["test_param_path_list"][0:3])
            + "/src"
        )
        dest = os.path.join(self.config["workDir"], "src")
        if is_dir(src):
            copyDirectory(src, dest)

    def _setup_args(self):
        if has_key(self.config, "CARDANO_ROOT"):
            self.cardano_root = self.config["CARDANO_ROOT"]
        self.sysroot = self.config["mini_sysroot"]
        self.lib_file = self.config["lib_file"]

    def _configure(self):
        self.common_compiler_flags = "-Wall -O0 -g3 -c -fmessage-length=0"
        self.common_linker_flags = ""

        self.include_dir = [self.config["workDir"] + "/"]
        self.lib_dir = []
        if has_key(self.config, "CARDANO_ROOT"):
            self.lib_dir.append(
                os.path.join(self.cardano_root, "lib", self.lib_file + ".o")
            )
            self.include_dir.append(os.path.join(self.cardano_root, "include"))

        VITIS_PATH = self.config["vitisPath"]

        cmdlist = [f"source {VITIS_PATH}/settings64.sh", f"cd {self.config['workDir']}"]

        self.console.runcmd_list(cmdlist)

    def compile(self, src_file_name):

        if has_key(self.config, "user_include_path"):
            for path in self.config.user_include_path:
                path = parse_config(self.config, path)
                self.include_dir += [path]

        self.include = ["-I" + dir for dir in self.include_dir]
        self.include = " ".join(self.include)

        compile_cmd = [
            self.app_name["compiler"][self.config["param"]],
            self.common_compiler_flags,
            self.app_name["compile_flags"],
            f'-MT"{self.srcDir}/{src_file_name}.cpp"',
            self.app_name["procname"][self.config["param"]],
            f'-MF"{self.srcDir}/{src_file_name}.d"',
            f'-MT"{self.srcDir}/{src_file_name}.o"',
            "-o",
            f'"{self.srcDir}/{src_file_name}.o"',
            f"{self.include}",
            f"{self.srcDir}/{src_file_name}.cpp",
        ]

        if has_key(self.config, "file_format") and self.config["file_format"] == "eabi":
            compile_cmd += [self.config["abi_cmd"]]

        cmd = " ".join(compile_cmd)
        self.console.runcmd(cmd)
        time.sleep(5)

    def link(self):

        if has_key(self.config, "user_lib_path"):
            for path in self.config.user_lib_path:
                path = parse_config(self.config, path)
                self.lib_dir += [path]

        self.lib = ["-L" + dir for dir in self.lib_dir]
        self.lib = " ".join(self.lib)

        link_cmd = [
            self.app_name["compiler"][self.config["param"]],
            "-v",
            self.app_name["procname"][self.config["param"]],
            self.common_linker_flags,
            f"{self.lib}",
            "-o",
            f"{self.config['workDir']}/aie_control.{self.app_name['exe']}",
            f"{self.srcDir}/aie_control.o",
        ]

        if has_key(self.config, "cardano_app") and self.config["cardano_app"]:
            link_cmd += [
                f'{self.wsDir}../cardano/work/src/{self.config["cardano_src"]}.o'
            ]

        if has_key(self.config, "file_format") and self.config["file_format"] == "eabi":
            link_cmd += [self.config["abi_cmd"]]

        link_cmd += [self.app_name["link_flags"]]

        cmd = " ".join(link_cmd)
        self.console.runcmd(cmd)
        time.sleep(5)

    def deploy(self):
        if has_key(self.config, "deploy_artifacts"):
            for artifact in self.config["deploy_artifacts"]:
                artifact_path = os.path.join(self.config["workDir"], artifact)
                if is_dir(artifact_path):
                    copyDirectory(
                        artifact_path, os.path.join(self.config["imagesDir"], artifact)
                    )
                elif is_file(artifact_path):
                    copy_file(artifact_path, self.config["imagesDir"])
            cmd_list = [
                f"cd {self.config['imagesDir']}",
                f"tar cvfJ deploy_artifacts.tar.xz ./*",
            ]
            self.console.runcmd_list(cmd_list)

        aie_path = os.path.join(
            self.config["workDir"], "aie_control." + self.app_name["exe"]
        )
        if is_file(aie_path):
            copy_file(aie_path, self.config["imagesDir"])
            log.info(f"{self.app_name['exe']} created successfully")
        else:
            raise Exception(f"Error: {self.app_name['exe']} creation failed")


def baremetal_runner(config, setup=True):
    ret = False
    try:
        app_name = {
            "compiler": {"a72": "aarch64-none-elf-g++", "r5": "armr5-none-eabi-g++"},
            "compile_flags": "-D__AIEBAREMTL__ -DPS_ENABLE_AIE -MMD -MP",
            "procname": {"a72": "-mcpu=cortex-a72", "r5": "-mcpu=cortex-r5"},
            "link_flags": "-ladf_api -Wl,--start-group,-lxil,-lgcc,-lc,-lstdc++,--end-group",
            "exe": "elf",
        }
        bm = CrossCompile(config, app_name, setup)
        # Baremetal application path for include and lib
        bm.component_ws_dir = (
            f"{bm.config['component_ws_dir']}/{bm.config['component']}/"
            + f"{bm.config['xsct_platform_name']}/"
            + f"{bm.config['xsct_proc_name']}/"
            + f"{bm.config['component']}_bsp/bsp/"
            + f"{bm.config['xsct_proc_name']}"
        )

        bm.ldscript = (
            f"{bm.config['component_ws_dir']}/{bm.config['component']}/"
            + f"{bm.config['component']}/src/lscript.ld"
        )

        bm.include_dir += [f"{bm.component_ws_dir}/include"]
        bm.compile("aie_control")
        bm.lib_dir += [f"{bm.component_ws_dir}/lib"]

        if config["HEAP_SIZE"]:
            bm.common_linker_flags += (
                f" -Xlinker --defsym=_HEAP_SIZE={config['HEAP_SIZE']} "
            )

        bm.common_linker_flags += f" -Wl,-T -Wl,{bm.ldscript}"
        bm.link()
        bm.deploy()
        ret = True
    except Exception as err:
        log.error(err)
    return ret


def linux_runner(config, setup=True):
    ret = False
    try:
        app_name = {
            "compiler": {"linux": "aarch64-linux-gnu-g++"},
            "compile_flags": "-DPS_INIT_AIE -DPS_ENABLE_AIE -DXAIE_DEBUG -MMD",
            "procname": {"linux": ""},
            "link_flags": "-lxaiengine -ladf_api -Wl,--warn-unresolved-symbols",
            "exe": "run",
        }
        bm = CrossCompile(config, app_name, setup)

        if config["cardano_app"]:
            config["src_path"] = "{wsDir}../cardano/images/"
            copyDirectory(f"{config['src_path']}", bm.config["workDir"])

        bm.include_dir += [f"{bm.sysroot}/usr/include/"]
        bm.include_dir += [f"{config['aie_headers_dir']}"]
        bm.compile("aie_control")

        if config["cardano_app"]:
            bm.srcDir = f"{config['wsDir']}../cardano/work/src"
            bm.compile(config["cardano_src"])
            bm.srcDir = f"{config['workDir']}/src"

        bm.lib_dir += [f"{config['aie_lib_dir']}"]
        bm.link()
        bm.deploy()
        ret = True
    except Exception as err:
        log.error(err)
    return ret
