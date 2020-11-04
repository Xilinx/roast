#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import logging
from roast.utils import *  # pylint: disable=unused-wildcard-import
from roast.component.basebuild import Basebuild
from roast.xexpect import Xexpect


log = logging.getLogger(__name__)


class BuildComponent(Basebuild):
    def __init__(self, config):
        super().__init__(config)
        self.component = config["component"]
        self.config = config

    def _setup(self):
        reset(self.wsDir)
        mkdir(self.workDir)
        mkdir(self.imagesDir)

    def build_xsct_app(self):
        print("Building %s" % self.component)
        elf_file = "%s/%s/Debug/%s.elf" % (self.workDir, self.component, self.component)
        # check for build_comp_sub_dir
        if self.config["external_embeddedsw"]:
            eswrepoPath = self.config["external_embeddedsw"]
        else:
            eswrepoPath = self.workDir + "git/"
            # FIXME: Use python module
            cmd = "git clone --reference %s/%s %s -b %s %s" % (
                self.config["gitReferenceUrl"],
                self.config["embeddedswReference"],
                self.config["embeddedswUrl"],
                self.config["embeddedswBranch"],
                eswrepoPath,
            )
            log.debug(f"cmd: {cmd}")
            runcmd(cmd, FileAdapter(log))
        copy_file(
            self.config["testXsa"], os.path.join(self.workDir, "design_1_wrapper.xsa")
        )

        # FIXME:move this to yaml

        procName = "psv_pmc_0"
        template = "versal " + self.config["component"].upper()
        if self.config["component"] == "psm":
            template += " Firmware"
            procName = "psv_psm_0"

        # FIXME: add as dictionary.
        # Donot hardcode xsa name
        app_cmd = "%s %s/build_app.tcl -pname %s " % (
            self.config["xsctCmd"],
            self.config["scriptsTclDir"],
            self.config["component"],
        )
        app_cmd += "-processor %s -osname standalone " % (procName)
        app_cmd += "-xsa %s/design_1_wrapper.xsa -ws %s " % (self.workDir, self.workDir)
        app_cmd += "-rp %s -app '%s'" % (eswrepoPath, template)
        runcmd(app_cmd, log)
        if is_file(elf_file):
            copy_file(elf_file, os.path.join(self.imagesDir, self.component + ".elf"))
            return True
        else:
            return False


def build(config) -> bool:
    # Fix logic to take defxsa if empty
    design = config["subtest"]
    testXsa = os.path.join(config["designs"][design], design + ".xsa")
    config["testXsa"] = testXsa

    bc = BuildComponent(config)
    return bc.build_xsct_app()


class BuildOsl(Basebuild):
    def __init__(self, config):
        super().__init__(config)

        self.component = config["component"]
        self.config = config

        self.src_path = None
        self.build_path = f'{config["workDir"]}/{self.component}-build/'
        self.console = Xexpect(log, exit_nzero_ret=True)
        self._setup(self.component)

    def _setup(self, component):
        self.src_reference = get_config_data(self.config, f"git.{component}.reference")
        self.external_src = self.config[f"external_{component}_src"]
        self.arch = self.config[f"{component}_arch"]
        self.compiler = self.config[f"{component}_compiler"]

        if has_key(self.config, f"{component}_defconfig"):
            self.defconfig = self.config[f"{component}_defconfig"]
        else:
            self.defconfig = None

        if has_key(self.config, f"{component}_devicetree"):
            self.console.runcmd(
                f"export DEVICE_TREE={self.config[f'{component}_devicetree']}"
            )

        self.console.runcmd(f"source {self.config['VITIS_SETTINGS_SH']}")
        self.console.runcmd(f"source {self.config['sysroot_env']}")
        # FIXME : Remove explicit addition of tools to env
        self.console.runcmd("export PATH=/group/siv2_xhd/work/lovek/tools/:$PATH")
        self.console.runcmd(f"export ARCH={self.arch}")
        self.console.runcmd(f"export CROSS_COMPILE={self.compiler}")
        mkdir(self.build_path)

        # export default env
        if has_key(self.config, f"{component}_env"):
            for env_var, value in self.config[f"{component}_env"].items():
                self.console.runcmd(f"export {env_var}={value}")

    def setup_src(self):
        if not self.external_src:
            self.console.runcmd(f"cd {self.config['workDir']}")

            clone(
                self.config.git_params[f"{self.component}"],
                f"{self.config['workDir']}/{self.component}",
                "build_osl.log",
                workDir=self.config["workDir"],
                reference=self.src_reference,
            )
            self.src_path = f"{self.config['workDir']}/{self.component}/"
        else:
            self.src_path = f"{self.external_src}"

    def configure(self):
        # configure the component
        if self.defconfig:
            cmd = f"make -C {self.src_path} {self.defconfig} O={self.build_path}"
            self.console.runcmd(cmd)

    def compile(self):
        extra_flags = ""
        if has_key(self.config, f"{self.component}_compile_flags"):
            extra_flags = f'{self.config[f"{self.component}_compile_flags"]}'
        if not self.config["outoftreebuild"]:
            self.build_path = self.src_path
        cmd = f'make -j {self.config["parallel_make"]} -C {self.src_path} O={self.build_path} {extra_flags}'
        self.console.runcmd(cmd, timeout=1000)

    def deploy(self):
        mkdir(self.config["deploy_artifacts"])
        for image in self.config[f"{self.component}_artifacts"]:
            image = parse_config(self.config, image)
            copy_file(
                os.path.join(self.build_path, image), self.config["deploy_artifacts"]
            )


class BuildDtb(BuildOsl):
    def __init__(self, config, variant=None, board=None):
        super().__init__(config)
        self.board = board
        self.variant = variant

    def compile(self):
        extra_flags = ""
        if has_key(self.config, f"{self.component}_compile_flags"):
            extra_flags = f'{self.config[f"{self.component}_compile_flags"]}'

        if self.config[f"{self.component}_buildtype"] == "dtg":
            self.tcl = os.path.join(self.config["ROOT"], "scripts/tcl/generate_dts.tcl")
            self.repo = os.path.join(self.config["workDir"], self.component)
            self.design = os.path.join(
                self.config[f"{self.component}_design"],
                self.variant,
                self.board,
                "system.xsa",
            )
            cmd = f'unset DISPLAY && {self.config["xsctCmd"]} {self.tcl} {self.design} {self.repo} {self.build_path} {self.config[f"{self.component}_dtg"]}'
        else:
            cmd = f"make dtbs -C {self.src_path} O={self.build_path} {extra_flags}"
        self.console.runcmd(cmd, timeout=1000)
        self.generate_dtb()

    def generate_dtb(self):
        if self.config[f"{self.component}_buildtype"] == "dtg":
            self.dts_path = os.path.join(
                self.build_path, self.config[f"{self.component}_dtg"]
            )
            self.console.runcmd(f"cd {self.dts_path}_dts")
            self.console.runcmd(
                f"cpp -Iinclude -E -P -x assembler-with-cpp system-top.dts | dtc -I dts -O dtb -o {self.config['system_dtb']}"
            )
