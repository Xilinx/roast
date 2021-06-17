#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import logging
import json
import os
import time
import shutil
from roast.utils import is_dir, remove, copyDirectory

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


def archive_artifacts(
    dest, copy_workdir=False, repo_path=os.getcwd(), src=None, silent_discard=True
):
    """This method copies images, logs directories from build directory to
    the specified destination path
    Parameters:
        src : source directory to be copied, will be copying build directory
              not mentioned
        dest : destination path
    """
    is_dir_check = False
    if src is None:
        src = os.path.join(repo_path, "build")
    if is_dir(dest):
        remove(dest)
        is_dir_check = True
    try:
        if not copy_workdir:
            copyDirectory(src, dest, ignore=shutil.ignore_patterns("work"))
        else:
            copyDirectory(src, dest)
        if is_dir_check:
            os.system(f"chmod -R 775 {dest}/*")
        else:
            os.system(f"chmod -R 775 {dest}")
    except Exception as err:
        if silent_discard:
            log.debug(err)
        else:
            raise Exception(err) from None


def discard_old_data(path, exclude_files=[], exclude_dirs=[], num_of_days=2):
    """This method cleans the directories if older than the mentioned num of
    days, from the given path
    Parameters:
        path : path from which directories are to be cleaned
        num_of_days : directories or files older than the specified num of
                      days will be deleted
    """
    num_of_days = 86400 * num_of_days
    timestamp = time.time()
    for r, dirs, files in os.walk(path):
        final_dirs, final_files = dirs, files
        for e in exclude_dirs:
            for d in dirs:
                if e in os.path.join(r, d):
                    final_dirs.remove(d)
        for e in exclude_files:
            for f in files:
                if e in os.path.join(r, f):
                    final_files.remove(f)
        for dir in final_dirs:
            try:
                mtime = os.lstat(os.path.join(r, dir)).st_mtime
                if timestamp - num_of_days > mtime:
                    remove(os.path.join(r, dir))
            except Exception as err:
                log.error(err)
        for file in final_files:
            try:
                mtime = os.lstat(os.path.join(r, file)).st_mtime
                if timestamp - num_of_days > mtime:
                    remove(os.path.join(r, file))
            except Exception as err:
                log.error(err)
