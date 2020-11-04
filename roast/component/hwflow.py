#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import sys
import re
import socket
import logging
from importlib import import_module
from roast.utils import *  # pylint: disable=unused-wildcard-import
from roast.component.basebuild import Basebuild

log = logging.getLogger(__name__)


class HwbuildRunner(Basebuild):
    def __init__(self, config):
        super(HwbuildRunner, self).__init__(config)

    def configure(self):
        super(HwbuildRunner, self).configure()
        self.vivado = self.config["VIVADO"]
        self.design_script = self.config["design_script"]
        self.design_path = self.workDir
        self.hwflow2_0 = False
        self.hwflow2_0_is_package = False
        self.hwflow_ver = self.config["hwflow_ver"]
        self.source = ""
        self.lsf = ""
        self.lsf_mode = self.config["lsf_mode"]
        self.lsf_options = self.config["lsf_options"]
        self.lsf_queue = self.config["lsf_queue"]
        self.lsf_osver = self.config["lsf_osver"]
        self.lsf_mem = self.config["lsf_mem"]
        self._setup()
        self._setup_vivado()

    def build(self):
        self.createhw()
        ret = self.deploy()
        return ret

    def _setup_vivado(self):
        self.env = os.environ.copy()
        self.env["PATH"] = get_dir_name(self.vivado) + ":" + self.env["PATH"]

    # Setup DesignEnv
    def _setup(self):
        if self.hwflow_ver == "2.0":
            self.hwflow2_0 = True
            if has_key(self.config, "hwflow_local"):
                self.source = {"file": self.config["hwflow_local"]}
                self._local_hw()
            else:
                # clone hwflow repo if hwflow package is not installed
                try:
                    import hwflow

                    copy_file(self.design_script, self.design_path)
                    self.hwflow2_0_is_package = True
                except ImportError:
                    self.source = {
                        "git": self.config["hwflow_url"],
                        "branch": self.config["hwflow_branch"],
                    }
                    self._clone_hw()

        else:
            if self.lsf_mode is True:
                self._setup_lsf_command()

            if has_key(self.config, "design_src"):
                self.source = self.config["design_src"]

                if has_key(self.source, "file"):
                    self._local_hw()
                elif has_key(self.source, "git"):
                    self._clone_hw()

        self.cwd = self.design_path

    # Setup LSF Command
    def _setup_lsf_command(self):
        site = socket.gethostname()[:3]
        if str(site).startswith("xhd"):
            bsub = self.config["lsf_xhdbsub"]
        elif str(site).startswith("xsj"):
            bsub = self.config["lsf_xsjbsub"]
        elif str(site).startswith("xir"):
            bsub = self.config["lsf_xirbsub"]
        else:
            bsub = self.config["lsf_xsjbsub"]

        bsub += (
            f" {self.lsf_options} -q {self.lsf_queue}"
            + f' -R "select[osver={self.lsf_osver}]"'
            + f' -R "rusage[mem={self.lsf_mem}]"'
        )
        self.lsf = bsub

    # Clone designs scripts from git repo.
    def _clone_hw(self):

        url = self.source["git"]
        branch = "master"  # Default branch to master
        if has_key(self.source, "branch"):
            branch = self.source["branch"]  # override user branch

        design_name = url.split("/").pop().split(".git", 1)[0]
        if self.hwflow2_0:
            self.design_path = os.path.join(self.workDir, "hwflow2_0")
            git_clone(url, self.design_path, branch)
            copy_file(self.design_script, self.design_path)
        else:
            self.design_path = os.path.join(self.workDir, design_name)
            git_clone(url, self.design_path, branch)
            if get_var(self.config, "design_relative_path"):
                self.design_path = (
                    f"{self.design_path}/{self.config.design_relative_path}"
                )
        os.chdir(self.design_path)

    # Set local design
    def _local_hw(self):
        hwfile = self.source["file"]
        design_name = hwfile.split("/").pop()
        if hwfile:
            if is_dir(hwfile) == True:
                self.design_path = f"{self.workDir}/{design_name}"
                copyDirectory(hwfile, self.design_path)
                os.chdir(self.design_path)
                if self.hwflow2_0:
                    copy_file(self.design_script, self.design_path)
            elif is_file(hwfile) == True:
                copy_file(hwfile, self.workDir)
            else:
                raise Exception(f"ERROR: {hwfile} does not exist")
        else:
            raise Exception("ERROR: FILE is empty")

    # Build design.
    def createhw(self):
        if self.hwflow2_0_is_package:
            design_script_dir = os.path.dirname(self.design_script)
            module_name, _ = os.path.splitext(os.path.basename(self.design_script))
            sys.path.append(f"{design_script_dir}")
            log.debug(f"Going to import module {module_name} ..")
            try:
                hwflow_module = import_module(module_name)
                if "main" in dir(hwflow_module):
                    # Add vivado to path, run vivado and remove vivado from path
                    _path_backup = os.environ.copy()["PATH"]
                    os.environ["PATH"] = self.env["PATH"]
                    hwflow_module.main()
                    os.environ["PATH"] = _path_backup
                    return True
                else:
                    log.debug(f"module {module_name} has no main() function")
            except ImportError:
                log.debug(f"Unable to import design script : {module_name}.py")

        if self.hwflow2_0:
            sys.path.append(f"{self.vivado}")
            self.design_module = get_base_name(self.design_script)
            runcmd_p(
                f"python3 {self.design_module}",
                log,
                env=self.env,
                cwd=self.cwd,
            )  # FIXME: This should call through current process
            return True

        elif is_file(self.design_script) == True:
            build_cmd = f"{self.vivado} -mode batch -source {self.design_script}"
            if has_key(self.config, "design_args"):
                build_cmd = f"{build_cmd} {self.config['design_args']}"

            if self.lsf_mode is True:
                build_cmd = f"{self.lsf} {build_cmd}"
            runcmd_p(build_cmd, log, env=self.env, cwd=self.cwd)
            return True

        else:
            log.error(f"{self.design_script} not exist in {self.workDir}")

        raise Exception("ERROR: Failed to build hwdesign")

    # Function to deploy design binaries.
    def deploy(self):

        # Copy artifacts to imagesDir
        if self.hwflow2_0 != True:
            log.info(f"Check design artifacts in {self.workDir}")
            ret = True

            if has_key(self.config, "artifacts"):
                artifacts = self.config["artifacts"]

                for image in artifacts:
                    image_file = find_file(image, self.workDir)
                    if image_file:
                        log.info(f"{image} exist in {self.workDir}")
                        copy_file(image_file, self.imagesDir)
                    else:
                        log.error(f"{image} not exist in {self.workDir}")
                        ret = False
        else:
            ret = self._deploy_hwflow2_0()
            if ret == False:
                raise Exception("ERROR: Failed to deploy artifacts")

        if has_key(self.config, "deploy_dir"):
            deploy_dir = self.config["deploy_dir"]
            if not is_dir(deploy_dir):
                mkdir(deploy_dir)
            copyDirectory(self.imagesDir, deploy_dir)

        return ret

    def _deploy_hwflow2_0(self):
        dir_list = get_dirs(os.getcwd())
        count = 0
        for name in dir_list:
            if re.search("hwflow_", name):
                design_name = name[7:]
                count += 1
        if count != 1:
            assert False, (
                f"ERROR: ${count} directories found" + " starting with hwflow_"
            )

        design_path = os.path.join(self.design_path, f"hwflow_{design_name}")
        xsa_path = os.path.join(design_path, "outputs", f"{design_name}.xsa")

        if is_file(xsa_path) == False:
            log.error("xsa not found in the design artifacts")
            return False
        if has_key(self.config, "artifacts"):
            artifacts = self.config["artifacts"]

            os.chdir(design_path)

            for image in artifacts:
                image = image.replace("@design", design_name)
                image_file = find_file(image, self.workDir)
                if image_file:
                    log.info(f"{image} exist in {self.workDir}")
                    if is_dir(image_file):
                        dir_name = os.path.basename(image)
                        copyDirectory(
                            image_file, os.path.join(self.imagesDir, dir_name)
                        )
                    else:
                        copy_file(image_file, self.imagesDir)
                else:
                    log.error(f"{image} not exist in {self.workDir}")

        return True


def hwrunner2(config):
    hw = HwbuildRunner(config)
    hw.createhw()
    ret = hw.deploy()
    return ret


# get test names from the directory where test module is present
def get_2_0_tests(file_path, sub_dir=None):
    dir_path = get_dir_name(get_abs_path(file_path))
    if sub_dir is not None:
        dir_path = os.path.join(dir_path, sub_dir)

    return get_files(dir_path, "py", basename=True)


# get testpath of the file
def get_design_path(config, script_name):
    test_path = config["test_path"]
    test_path = os.path.join(test_path, script_name + ".py")
    return test_path
