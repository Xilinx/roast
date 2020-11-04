#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import glob
import logging
from roast.utils import *  # pylint: disable=unused-wildcard-import
from roast.xexpect import Xexpect
from roast.component.basebuild import Basebuild
from roast.component.xsct import buildapp as xsct
from roast.component.crosscompile.crosscompile import baremetal_runner
from roast.component.bif.generate import pdi

log = logging.getLogger(__name__)


class Cardano(Basebuild):
    def __init__(self, config):
        super(Cardano, self).__init__(config)
        self.console = Xexpect(log, exit_nzero_ret=True)
        self.srcDir = f"{self.workDir}/src/"
        self.cdoDir = f"{self.workDir}/Work/ps/cdo/"
        self.control_cpp = f"{self.workDir}/Work/ps/c_rts/aie_control.cpp"

    def compile_cardano_app(self):

        CARDANO_ROOT = self.config["CARDANO_ROOT"]
        XLNX_LICENSE = self.config["XILINXD_LICENSE_FILE"]
        CARDANO_APP_CDO_FLAGS = self.config["CARDANO_APP_CDO_FLAGS"]

        cmdlist = [
            f"export CARDANO_ROOT={CARDANO_ROOT}",
            f"export XILINXD_LICENSE_FILE={XLNX_LICENSE}",
            f"source {CARDANO_ROOT}/scripts/cardano_env.sh",
            f"cd {self.workDir}",
        ]
        self.console.runcmd_list(cmdlist)

        # compile cardano and generate cdo
        compile_cmd = [
            "aiecompiler --device",
            self.config["DEVICE"],
            "-phydevice",
            self.config["PHYDEVICE"],
            self.config["CARDANO_FLAGS"],
            f'-include="{self.srcDir}/kernels"',
            f'-include="{self.srcDir}"',
            f'{self.srcDir}/{self.config["cardano_src"]}.cpp',
        ]
        cmd = " ".join(compile_cmd)
        self.console.runcmd(cmd, timeout=300)

    def generate_cdo(self):
        CARDANO_APP_CDO_FLAGS = self.config["CARDANO_APP_CDO_FLAGS"]
        cmd = f"{self.cdoDir}/generateAIEConfig {CARDANO_APP_CDO_FLAGS}"
        self.console.runcmd(cmd, timeout=250)

    def generate_pdis(self):
        self.config["console"] = self.console
        assert pdi(self.config, "new"), "ERROR: PDI Generation failed"

    def copy_images(self):
        ret = False
        try:
            mkdir(f"{self.imagesDir}/elfs")
            mkdir(f"{self.imagesDir}/src")
            self.elfs = glob.glob(f"{self.workDir}/Work/aie/{self.config['tiles']}")
            for elf in self.elfs:
                name = os.path.basename(elf)
                copy_file(f"{elf}/Release/{name}", f"{self.imagesDir}/elfs")
            copy_file(f"{self.cdoDir}/aie_cdo.bin", f"{self.imagesDir}")
            copy_file(f"{self.control_cpp}", f"{self.imagesDir}/src")
            ret = True
        except Exception as err:
            log.error(err)
        return ret


def cardano_builder(config):
    btc = Cardano(config)
    btc.compile_cardano_app()
    btc.generate_cdo()
    assert btc.copy_images(), "ERROR: Build Cardano Failed!"
    btc.generate_pdis()


def generate_pdi_aie(config):
    bc = Basebuild(config)
    copyDirectory(config["elfs_path"], config["imagesDir"])
    assert pdi(config), "ERROR: PDI Generation failed"


def standalone_builder(config):
    xsct.xsct_builder(config)
    copyDirectory(config["elfs_path"], config["imagesDir"])
    assert pdi(config), "ERROR: PDI Generation failed"


def baremetal_lib(config, proc):
    overrides(config, "std")
    overrides(config, proc)
    xsct.xsct_builder(config)
    return True


def baremetal_builder(config, proc):
    overrides(config, "std")
    overrides(config, proc)
    return baremetal_runner(config)


def baremetal_cardano_builder(config):
    xsct.xsct_builder(config)
    baremetal_runner(config, setup=False)
    copyDirectory(config["elfs_path"], config["imagesDir"])
    assert pdi(config)


def check_cardano(config):
    if is_dir(f'{config["test_path"]}/cardano'):
        config["cardano_app"] = True
    else:
        config["cardano_app"] = False
