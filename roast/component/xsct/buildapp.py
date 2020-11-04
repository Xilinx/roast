#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import sys
import yaml
import shlex
import shutil
import inspect
import argparse
import subprocess
import logging
from roast.utils import *  # pylint: disable=unused-wildcard-import
from roast.component.basebuild import Basebuild
from roast.xexpect import Xexpect

log = logging.getLogger(__name__)


def getdict(data):
    flags = data.split(",")
    dict_out = {}
    for eachflag in flags:
        ele_list = eachflag.split(":")
        ele_list = stripper(ele_list)
        dict_out[ele_list[0]] = {ele_list[1]: ele_list[2]}
    return dict_out


def verify_extra_args(extra_args):
    if (extra_args is None) or len(extra_args) == 0 or (extra_args)[0] == "":
        return 0
    return 1


def write_extra_args_to_yaml_conf(args, input, appconfig, bspconfig, yaml_file_path):
    # remove the yaml config file if exists
    remove(yaml_file_path)

    # write apps configuration to the yamlconfig file
    final_conf = {}
    app = {}
    app_args = {}
    bsp = {}
    bsp_args = {}

    if input == "file":
        for arg in args.keys():
            if arg in appconfig:
                app_args[arg] = args[arg]
            elif arg in bspconfig:
                bsp_args[arg] = args[arg]

    if input == "cmdline":
        extra_args = "".join(args["extra_args"])
        received = getdict(extra_args)

        for key in received:
            if key in appconfig:
                app_args[key] = received[key]
            elif key in bspconfig:
                bsp_args[key] = received[key]

    if app_args:
        app["app"] = app_args
        final_conf.update(app)

    if bsp_args:
        bsp["bsp"] = bsp_args
        final_conf.update(bsp)

    if final_conf:
        print_msg("YAMLCONF.YAML")
        write_to_yaml(final_conf, yaml_file_path, False)
        return True


class AppBuilder(Basebuild):
    def __init__(self, config, setup: bool = True):

        super().__init__(config, setup=setup)
        if has_key(config, "console"):
            self.console = config["console"]
        else:
            self.console = Xexpect(log, exit_nzero_ret=True)
            config["console"] = self.console

        self.config_var_dict = self.set_config_var()
        self.defconfig_var_dict = self.set_defconfig_var()
        self.supported_components_list = self.get_defconfig_var().keys()
        self.user_var_dict = ""
        self.yaml_file_path = ""
        self.CONFIG_FILE_SET = False
        self.extra_env = ["scriptsDir"]
        self.cmd = ""
        self.config_var()

    def set_config_var(self):
        """Loads config.yaml from absolute path set in configuration.
        If path not set in configuration, use config.yaml included in library.
        """

        if has_key(self.config, "XSCT_CONFIG"):
            xsct_path = self.config["XSCT_CONFIG"]
        else:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            xsct_path = os.path.join(dir_path, "config.yaml")
        data = load_yaml(xsct_path)
        if data is None or data == "":
            print_err_exit("File: config.yaml is empty or not found")
        for key in data:
            data[key] = set(data[key])
        return data

    def config_var(self):
        """Exports configuration variables needed by tcl scripts.
        If scriptsDir is not specified in config, use this file's directory.
        """

        if not has_key(self.config, "scriptsDir"):
            self.config["scriptsDir"] = os.path.dirname(os.path.realpath(__file__))

        if has_key(self.config, "extra_xsct_env"):
            if isinstance(self.config["extra_xsct_env"], list):
                self.extra_env.extend(self.config["extra_xsct_env"])
            else:
                self.extra_env.extend(self.config["extra_xsct_env"].split(" "))

        for key in self.extra_env:
            value = self.config[key]
            self.console.runcmd(f"export {key}={value}")

    def set_defconfig_var(self):
        """Loads defconfig.yaml from absolute path set in configuration.
        If path not set in configuration, use defconfig.yaml included in library.
        """

        if has_key(self.config, "DEFAULT_XSCT_CONFIG"):
            defconfig_path = self.config["DEFAULT_XSCT_CONFIG"]
        else:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            defconfig_path = os.path.join(dir_path, "defconfig.yaml")
        data = load_yaml(defconfig_path)
        if data is None or data == "":
            err_msg = "defconfig.yaml is empty or not found or file reading failed"
            log.error(err_msg)
            raise Exception(err_msg)

        # Find the supported components
        valid_components = list(data.keys())

        # Remove the common key from the supported components
        del_element("common", valid_components)

        # Add the common variables to each component
        for component in valid_components:
            try:
                # Find the common dictionary values in common Vs specified component
                common_vals = list(
                    set(data["common"].keys()) & set(data[component].keys())
                )

                # Check if there are some common values present in common and individual component
                correction = {}
                for val in common_vals:
                    correction[val] = data[component][val]

                # Update the data with the common values
                data[component].update(data["common"])

                # Apply the correction
                data[component].update(correction)
            except:
                print_err_exit("Setting defconfig variables failed !")

        del_key("common", data)

        return data

    def get_user_args(self, argv=None):

        parser = argparse.ArgumentParser(
            description="This script is used to build elf for any component using xsct"
        )
        parser.add_argument("--app", help="App Name to be build")
        parser.add_argument("--arch", default="64", help="Platform Architecture")
        parser.add_argument("--bspname", help="Standalone BSP Name")
        parser.add_argument(
            "--component",
            choices=self.get_supported_components(),
            help="Supported Components",
        )
        parser.add_argument(
            "--do_compile", default="1", choices=["0", "1"], help="Build the project"
        )
        parser.add_argument(
            "--do_cleanup",
            default="1",
            choices=["0", "1"],
            help="Clean up after building the project",
        )
        parser.add_argument("--driver", help="Driver Name to be build")
        parser.add_argument("--elf_name", help="Cumtome Elf Name to be used")
        parser.add_argument("--example_name", help="Example to be build")
        parser.add_argument("--extension", help="Run time functions to perform")
        parser.add_argument("--extra_args", nargs="*")
        parser.add_argument("--file", type=open, action=LoadFromFile)
        parser.add_argument("--hdf", help="Path of the directory containing hdf")
        parser.add_argument("--hwpname", default="hw0", help="Name of HW project")
        parser.add_argument("--lib", help="Libraries Required")
        parser.add_argument("--library_name", help="Library name to be build")
        parser.add_argument("--thirdparty_name", help="ThirdParty name to be build")
        parser.add_argument(
            "--thirdparty_dir", help="ThirdParty Directory where apps/libs are present"
        )
        parser.add_argument("--osname", default="standalone", help="Operating System")
        parser.add_argument(
            "--out_dir", help="Output directory path where elfs needs to be copied"
        )
        parser.add_argument("--pname", help="Name of the project")
        parser.add_argument("--processor", help="Processor used for compilation")
        parser.add_argument("--rp", help="Repo Path")
        parser.add_argument("--rp_intg", help="INTG Repo Path")
        parser.add_argument(
            "--import_sources",
            help="Path of directory where source to be imported is present",
        )
        parser.add_argument(
            "--import_args", help='"Import sources arguments like : -soft-link, etc'
        )
        parser.add_argument("--ws", help="Workspace used for compilation")
        parser.add_argument("--xsct_path", help="Xsct Bin Path")
        parser.add_argument("--functest_name", help="Name of the function test")
        parser.add_argument(
            "--build_till_bsp", default="0", choices=["0", "1"], help="Build bsp only"
        )

        args = parser.parse_args(argv)
        # Fixme: convert args to type class dict before retunring it
        return args

    def map_procname(self, proc):
        proc_dict = {
            "a72_0_versal": "psv_cortexa72_0",
            "a72_1_versal": "psv_cortexa72_1",
            "r5_0_versal": "psv_cortexr5_0",
            "r5_1_versal": "psv_cortexr5_1",
            "pmc_versal": "psv_pmc_0",
            "psm_versal": "psv_psm_0",
            "a53_0_zynqmp": "psu_cortexa53_0",
            "a53_1_zynqmp": "psu_cortexa53_1",
            "r5_0_zynqmp": "psu_cortexr5_0",
            "r5_1_zynqmp": "psu_cortexr5_1",
            "a9_0_zynq": "ps7_cortexa9_0",
            "a9_1_zynq": "ps7_cortexa9_1",
            "mb_0": "microblaze_0",
        }
        if proc in proc_dict.keys():
            return proc_dict[proc]
        else:
            return proc

    def parser(self, config):
        args = {}
        if has_key(config, "do_compile"):
            args["do_compile"] = config["do_compile"]
        else:
            args["do_compile"] = 1
        if has_key(config, "do_cleanup"):
            args["do_cleanup"] = config["do_cleanup"]

        if has_key(config, "extension"):
            args["extension"] = config["extension"]

        if has_key(config, "xsct_proj_name"):
            args["pname"] = config["xsct_proj_name"]

        if has_key(config, "xsct_proc_name"):
            args["processor"] = self.map_procname(config["xsct_proc_name"])

        if has_key(config, "XSCT_PATH"):
            args["xsct_path"] = config["XSCT_PATH"]

        if has_key(config, "xsct_os_name"):
            args["osname"] = config["xsct_os_name"]

        if has_key(config, "xsct_xsa"):
            args["hdf"] = config["xsct_xsa"]

        if has_key(config, "xsct_app_name"):
            args["app"] = config["xsct_app_name"]

        if has_key(config, "xsct_platform_name"):
            args["hwpname"] = config["xsct_platform_name"]

        if has_key(config, "build_till_bsp"):
            args["build_till_bsp"] = config["build_till_bsp"]
        else:
            args["build_till_bsp"] = 0

        if has_key(config, "extra_args"):
            args["extra_args"] = config["extra_args"]
        else:
            args["extra_args"] = None

        if has_key(config, "xsct_outDir"):
            args["out_dir"] = config["xsct_outDir"]
        else:
            args["out_dir"] = f"{self.wsDir}/images"

        if has_key(config, "xsct_elf_name"):
            args["elf_name"] = config["xsct_elf_name"]

        if has_key(config, "xsct_lib"):
            args["lib"] = config["xsct_lib"]

        if has_key(config, "xsct_library_name"):
            args["library_name"] = config["xsct_library_name"]

        if config["xsct_import_sources"]:
            args["import_sources"] = config["xsct_import_sources"]

        if config["xsct_import_args"]:
            args["import_args"] = config["xsct_import_args"]

        if has_key(config, "xsct_thirdparty_name"):
            args["thirdparty_name"] = config["xsct_thirdparty_name"]

        if has_key(config, "xsct_thirdparty_dir"):
            args["thirdparty_dir"] = config["xsct_thirdparty_dir"]

        if has_key(config, "xsct_extention_tcl"):
            if config["xsct_extention_tcl"]:
                args["extension"] = config["xsct_extention_tcl"]

        if has_key(config, "component"):
            args["component"] = config["component"]

        if has_key(config, "xsct_driver"):
            args["driver"] = config["xsct_driver"]

        if has_key(config, "xsct_example_name"):
            args["example_name"] = config["xsct_example_name"]

        if has_key(config, "repo_exists") and config["repo_exists"] == 1:
            args["rp"] = f"{self.workDir}/src/"
        else:
            if config["externalEmbeddedsw"]:
                args["rp"] = config["externalEmbeddedsw"]

        args["ws"] = f"{self.workDir}/{config['component']}/"

        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.console.runcmd(f"export SCRIPTS_PYTHON={dir_path}")
        self.console.runcmd(f"export test_log_path={self.wsDir}/logs")
        self.console.runcmd(f"export test_work_path={self.wsDir}/work")
        self.console.runcmd(f"export test_image_path={self.wsDir}/images")

        if has_key(config, "BUILD_SOURCE"):
            self.console.runcmd(f"export BUILD_SOURCE={config['BUILD_SOURCE']}")

        if has_key(config, "usr_src_path"):
            self.console.runcmd(f"export usr_src_path={config['usr_src_path']}")

        return args

    def set_user_args(self, args):
        # Extra args might be present in config file
        appconfig = self.get_config_var()["APP_CONFIG"]
        bspconfig = self.get_config_var()["BSP_CONFIG"]
        yaml_file_path = os.path.join(self.workDir, "yamlconf.yaml")

        if verify_extra_args(args["extra_args"]):
            if write_extra_args_to_yaml_conf(
                args, "cmdline", appconfig, bspconfig, yaml_file_path
            ):
                self.CONFIG_FILE_SET = True
                self.yaml_file_path = yaml_file_path
        elif args["extra_args"] is None:
            if write_extra_args_to_yaml_conf(
                args, "file", appconfig, bspconfig, yaml_file_path
            ):
                self.CONFIG_FILE_SET = True
                self.yaml_file_path = yaml_file_path

        # Verify if all the mandatory args are defined
        is_defined(args, list(self.get_config_var()["MANDATORY_ARGS"]))

        arg_dict = {}
        for arg in args.keys():
            value = args[arg]
            if value is not None and value != "":
                arg_dict[arg] = value

        # Collect few mandatory args
        if "xsct_path" not in arg_dict:
            arg_dict["xsct_path"] = self.config["xsctCmd"]
        if "rp" not in arg_dict:
            arg_dict["rp"] = self.config["ESW_REPO"]

        # Collect the params from the default settings
        component = arg_dict["component"]
        config_dict = self.get_defconfig_var()
        for key in config_dict:
            if key == component:
                subdict = config_dict[key]
                for subkey in subdict:
                    if subkey not in arg_dict:
                        arg_dict[subkey] = subdict[subkey]

        self.user_var_dict = arg_dict

    def set_cmd(self):
        user_var_dict = self.get_user_var()
        tclargs = self.get_config_var()["TCL_SUPPORTED_ARGS"]
        cmd = ""
        for key in user_var_dict:
            if key in tclargs:
                value = user_var_dict[key]
                if value is not None and value != "":
                    str1 = "-" + str(key)
                    str2 = surround_double_quotes(str(value))
                    cmd += str1 + " " + str2 + " "

        dir_path = os.path.dirname(os.path.realpath(__file__))
        app_path = os.path.join(dir_path, self.config["APP_TCL"])

        cmd = str(user_var_dict["xsct_path"]) + " " + app_path + " " + cmd + " "

        if self.get_config_file():
            cmd += "-yamlconf" + " " + surround_double_quotes(self.get_yaml_file())

        self.cmd = cmd

    # Getter
    def get_config_var(self):
        return self.config_var_dict

    def get_defconfig_var(self):
        return self.defconfig_var_dict

    def get_supported_components(self):
        return self.supported_components_list

    def get_user_var(self):
        return self.user_var_dict

    def get_config_file(self):
        return self.CONFIG_FILE_SET

    def get_yaml_file(self):
        return self.yaml_file_path

    def get_cmd(self):
        return self.cmd

    def build_app(self, config) -> bool:

        self.set_cmd()
        cmd = self.get_cmd()
        log.info(f"APP.TCL COMMAND: {cmd}")

        if has_key(config, "source_cardano") and config["source_cardano"] == 1:

            CARDANO_ROOT = config["CARDANO_ROOT"]
            self.console.runcmd(f"export CARDANO_ROOT={CARDANO_ROOT}")
            self.console.runcmd(f"source {CARDANO_ROOT}/scripts/cardano_env.sh")

        self.console.runcmd("unset DISPLAY")
        self.console.runcmd(
            f"export _JAVA_OPTIONS='-Duser.home={config['workDir']}/.xsct'"
        )
        self.console.runcmd(cmd, timeout=1500)
        if config["build_till_bsp"] or check_if_string_in_file(
            f"{self.wsDir}/images/results.txt", "PASS"
        ):
            return True
        else:
            self.console.logfile.error("ELF creation Failed")
            return False


def xsct_builder(config, setup=True):
    builder = AppBuilder(config, setup=setup)
    builder.configure()
    args = builder.parser(config)
    builder.set_user_args(args)
    return builder.build_app(config)
