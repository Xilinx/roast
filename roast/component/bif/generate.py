#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import re
import logging
from collections import namedtuple
from roast.xexpect import Xexpect
from roast.component.basebuild import Basebuild
from roast.utils import has_key, is_file, copy_file, remove

log = logging.getLogger(__name__)


# Data containers for bif generation
Header = namedtuple("Header", ["header", "name", "args"])
Header.__new__.__defaults__ = ("image", None, None)
Component = namedtuple("Component", ["name", "params"])
Block = namedtuple("Block", ["header", "components"])


def bifstring(bifstr: str, value: str, config) -> str:
    # Get the design name
    if has_key(config, "designs"):
        design = config["designs"].split("/")[-2]

    if re.search(r"ext=", value):
        bifstr += config["designs"] + "outputs/" + f"{design}.{value.split('=')[1]}"
    elif re.search(r"rel=", value):
        bifstr += config["imagesDir"] + f"{value.split('=')[1]}"
    elif re.search(r"path=", value):
        config["tmpvalue"] = value.split("=")[1]
        bifstr += config["tmpvalue"]
    else:
        config["tmpvalue"] = value
        bifstr += config["tmpvalue"]
    return bifstr


def create_partition(id, type_data, extra_args, image_path) -> str:
    str_component = (
        f"  partition \n"
        f"  {{\n"
        f"      id = {hex(id)}\n"
        f"      {type_data} {extra_args}\n"
        f"      file = {image_path}\n"
        f"  }}\n"
    )
    return str_component


def generate_bif(config, format_type: str) -> None:
    bif_path = os.path.join(config["workDir"], config["bifFile"])
    with open(bif_path, "w") as biffile:
        if format_type == "new":
            defdata = {
                "plm": ["type = bootloader", "path"],
                "pmccdo": ["type = pmcdata,load=0xF2000000", "path"],
                "cdo": ["type = cdo", "path"],
                "sys_dtb": ["load=0x1000", "path"],
                "linux_image": ["load=0x2000000", "path"],
                "uboot": ["", "path"],
                "puf": ["puf_file", "path"],
                "aie-elf": ["core = aie", "path"],
                "psm": ["core = psm", "psmElf"],
                "a72": ["core = a72-0", "path"],
                "r5": ["core = r5-0", "path"],
                "a72_1": ["core = a72-1", "path"],
                "r5_1": ["core = r5-1", "path"],
                "r5_lock": ["core = r5-lockstep", "path"],
            }
            subsys_data = {
                "pmc_subsys": "0x1c000001",
                "lpd_subsys": "0x4210002",
                "pl_cfi_subsys": "0x18700000",
                "aie_subsys": "0x421c005",
                "fpd_subsys": "0x420c003",
                "subsystem": "0x1c000000",
            }
            biffile.write("new_bif:\n{\n")
            id_code = "0x04ca8093"
            extended_id_code = "0x01"
            if has_key(config, "id_code"):
                id_code = config["id_code"]
            if has_key(config, "extended_id_code"):
                extended_id_code = config["extended_id_code"]
            if has_key(config, "bootheader"):
                biffile.write(config["bootheader"].format())
            biffile.write(
                f" id_code = {id_code}\n extended_id_code = {extended_id_code} \n id = 0x1\n"
            )
            id = 2
            headers, l_components = zip(*config.bif)
            for header, components in zip(headers, l_components):
                # config library returns list so cast back to namedtuple
                header = Header(*header)
                components = [Component(*component) for component in components]
                if header.header == "image":
                    subsystem_id = subsys_data[header.name]
                    biffile.write(
                        f" {header.header}\n {{\n  name = {header.name}\n  id = {subsystem_id}\n"
                    )
                    if header.args:
                        biffile.write(f"  {header.args}\n")
                    for component in components:
                        extra_args = bifstring(
                            "", "".join(component.params[:-1]), config
                        )
                        image_path = bifstring("", component.params[-1], config)
                        str_component = create_partition(
                            id, defdata[component.name][0], extra_args, image_path
                        )
                        biffile.write(str_component)
                elif header.header == "metaheader":
                    for component in components:
                        extra_args = bifstring(
                            "", "".join(component.params[:-1]), config
                        )
                        str_component = (
                            f"\n  metaheader \n"
                            f"  {{\n"
                            f"    {extra_args}\n"
                            f"  }}\n"
                        )
                        biffile.write(str_component)
                biffile.write(" }\n")
                id = id + 1
            biffile.write("}\n")
        elif format_type == "old":
            defdata = {
                "plm": ["bootloader", "path"],
                "pmccdo": ["pmcdata,load=0xF2000000", "path"],
                "cdo": ["partition_type=cdo", "path"],
                "aie-elf": ["destination_cpu=aie", "path"],
                "psm": ["destination_cpu=psm", "psmElf"],
                "a72": ["destination_cpu=a72-0", "path"],
                "r5": ["destination_cpu=r5-0", "path"],
            }
            if config["boot_header"]:
                biffile.write(f"{config['boot_header']}" ":\n{\n")
            else:
                biffile.write("all:\n{\n")
            for image in config["bif"]:
                comp = image[0]
                value = image[1]
                bifstr = "[{}] ".format(defdata[comp][0])
                bifstr = bifstring(bifstr, value, config)
                bifstr = "\t{}\n".format(bifstr)
                biffile.write(bifstr)
            biffile.write("}\n")

    if is_file(bif_path):
        copy_file(
            bif_path,
            os.path.join(config["imagesDir"], config["bifFile"]),
        )
        log.info("Bif Generated successfully")
    else:
        err_msg = "Bif generation failed"
        log.error(err_msg)
        raise Exception(err_msg)


def generate_pdi(config) -> None:

    if has_key(config, "console"):
        console = config["console"]
    else:
        console = Xexpect(log)
        config["console"] = console

    remove(os.path.join(config["imagesDir"], config["pdiFile"]))
    if is_file(config["bifFile"]):
        copy_file(config["bifFile"], config["imagesDir"])

    console.runcmd(f"cd {config['imagesDir']}")
    bootgen_cmd = [
        config["bootgenCmd"],
        "-arch",
        config["platform"].lower(),
        config["bootgenExtraArgs"],
        "-log",
        "info",
        "-image",
        config["bifFile"],
        "-o",
        config["pdiFile"],
    ]
    cmd = " ".join(bootgen_cmd)
    console.runcmd(cmd, expected="Bootimage generated successfully")

    if is_file(os.path.join(config["imagesDir"], config["pdiFile"])):
        log.info("PDI generated successfully")
    else:
        err_msg = f"{config['pdiFile']} creation failed"
        log.error(err_msg)
        raise Exception(err_msg)


def gen_boot_bin(config) -> None:

    if has_key(config, "console"):
        console = config["console"]
    else:
        console = Xexpect(log)
        setattr(config, "console", console)

    remove(os.path.join(config["imagesDir"], config["binFile"]))
    if config["bifFile"]:
        copy_file(config["bifFile"], config["imagesDir"])

    console.runcmd(f"cd {config['imagesDir']}")

    bootgen_cmd = [
        config["bootgenCmd"],
        "-arch",
        config["platform"].lower(),
        config["bootgenExtraArgs"],
        "-log",
        "info",
        "-image",
        config["bifFile"],
        "-o",
        config["binFile"],
    ]
    cmd = " ".join(bootgen_cmd)
    console.runcmd(cmd, expected="Bootimage generated successfully")

    if is_file(os.path.join(config["imagesDir"], config["binFile"])):
        log.info("Bootable Image generate successful")
    else:
        err_msg = f"{config['binFile']} creation failed"
        log.error(err_msg)
        raise Exception(err_msg)


def pdi(config, format_type: str = "new") -> bool:
    ret = False
    try:
        generate_bif(config, format_type=format_type)
        generate_pdi(config)
        ret = True
    except Exception as err:
        log.error(err)
    return ret


def bin(config, format_type: str = "old") -> bool:
    ret = False
    try:
        generate_bif(config, format_type=format_type)
        gen_boot_bin(config)
        ret = True
    except Exception as err:
        log.error(err)
    return ret
