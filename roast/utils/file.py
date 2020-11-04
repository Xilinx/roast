#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import logging
import json

log = logging.getLogger(__name__)


def read_json(file_path):
    """function that returns the json dictionary object by reading a json file

    Args:
        file_path (str): path to json file

    Returns:
        dict: retrun the JSON data
    """
    try:
        with open(file_path) as db_file_handle:
            try:
                data = json.load(db_file_handle)
                return data
            except ValueError:
                log.error(f"Invalid JSON file {file_path}")
                raise ValueError
            except TypeError:  # NoneType
                log.error(f"Reading {file_path} returned TypeErr")
                raise TypeError
    except IOError:
        log.error(f"Unable to open : {file_path}")
        raise IOError


def write_json(file_path, data, sort=True):
    """function that dictionary object to a file

    Args:
        file_path (str): path to json file to be written to
        data (dict): data to write
        sort (bool, optional): Sort based on keys. Defaults to True.
    """
    try:
        with open(file_path, "w") as db_file_handle:
            json.dump(
                data, db_file_handle, sort_keys=sort, separators=(",", ": "), indent=4
            )
    except IOError:
        log.error(f"Unable to write to : {file_path}")
        raise IOError
