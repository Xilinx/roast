#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import sys
import git
import fileinput
import shutil
import inspect
import argparse
import re
import random
import string
from filelock import FileLock
import itertools, collections.abc
import yaml
import subprocess
import atexit
from pathlib import Path
from distutils.dir_util import copy_tree

from typing import Any, List, Optional, Dict
from warnings import warn


class Git:
    def __init__(self, git_params, repo_path, clone_once, logfile):
        self.repo = None
        self.repo_url = git_params.url
        self.branch = git_params.branch
        self.sparse_path = git_params.sparse_path
        self.patches = git_params.patches
        self.patchesDir = git_params.patchesDir
        self.rev = git_params.rev
        self.repo_path = repo_path
        self.logfile = logfile
        self.clone_once = clone_once

    def clone(self, **kwargs):
        self.repo_name = get_base_name(self.repo_path)
        self.base_path = get_dir_name(self.repo_path)
        self.lock_path = os.path.join(self.base_path, f".{self.repo_name}.lock")
        self.git_path = os.path.join(self.repo_path, ".git")
        self.repo_cloned = False
        self.lock = FileLock(self.lock_path)
        with self.lock:
            if (self.clone_once and not is_dir(self.git_path)) or not self.clone_once:
                self._clone(**kwargs)
                self.repo_cloned = True

    def _clone(self, **kwargs):

        no_checkout = True if len(self.sparse_path) else False
        git.Repo.clone_from(
            self.repo_url,
            self.repo_path,
            branch=self.branch,
            no_checkout=no_checkout,
            **kwargs,
        )

        self.repo = git.Repo(self.repo_path)
        if len(self.sparse_path):
            with self.repo.config_writer() as cw:
                cw.set_value("core", "sparseCheckout", "true")
            checkout_path = os.path.join(self.repo_path, ".git/info/sparse-checkout")
            with open(checkout_path, "w") as fd:
                fd.writelines(self.sparse_path)
            self.repo.git.checkout(self.branch)

        self.last_hash = self.repo.git.rev_parse(["--verify", "HEAD"])
        self.origin_commit = self.repo.git.log(
            "-n 1", "--pretty=format:%H - %an, %ar : %s"
        )
        if kwargs.get("recurse_submodules") == "latest":
            for submodule in self.repo.submodules:
                submodule.update(init=True)
                sub_repo = submodule.module()
                sub_repo.git.pull()

    def checkout(self):
        if self.rev:
            self.repo.git.checkout(self.rev)
            self.last_hash = self.repo.git.rev_parse(["--verify", "HEAD"])

    def apply_patch(self, workDir):

        patches = []
        if self.patches and is_dir(f"{workDir}/patches"):
            patches = [
                os.path.join(f"{workDir}/patches", patch) for patch in self.patches
            ]

        if is_dir(self.patchesDir):
            external_patches = get_files(
                self.patchesDir, extension="patch", abs_path=True
            )
            patches.extend(external_patches)

        for patch in patches:
            if is_file(patch):
                self.repo.git.am(["-3", patch])

    def clean(self):
        self.repo.git.clean("-xdf")

    def run_gitcmd(self, cmd, logger=None, ret_out=False):
        """Run the git command specified by the cmd input, in the specified repo
        path.

        Args:
            cmd (str): the git command to be executed
            logger (logging.getLogger, optional): logger object
            ret_out (bool, optional): decides if the output of git commands need
                     to be returned for further processing. Defaults to False.

        Returns:
            boolean/list: pass fail status of git command/ [status,
                            output,error] from the command
        """
        g = git.cmd.Git(os.path.realpath(self.repo_path))
        cmd_list = cmd.split()
        stat, out, err = g.execute(cmd_list, with_extended_output=True)
        if logger is not None:
            logger.debug(out)
        if ret_out:
            return stat, out, err
        return stat

    def git_update_repo(
        self, branch=None, commit=None, tag=None, logger=None, ret_out=False
    ):
        """Updates the user provided repo to user specified tag or branch
            or (branch and optional commit ID)
            Note: if no tag, branch, commit is provided it updates the repo to
            its latest master branch

        Args:
            branch (str, optional): branch name to check out. Defaults to None.
            commit (str, optional): commit sha to check out, to be used with
                    valid branch. Defaults to None.
            tag (str, optional): tag that needs to be checked out. Defaults to None.
            logger (logging.getLogger, optional): logger object. Defaults to None.
            ret_out (bool, optional): boolean that decides if deatiled output of
                    updating need to be returned. Defaults to False.

        Returns:
            boolean/list: pass fail status of repo update/ [status, output]
                            list from the command
        """
        status = False
        out = ""
        if not self.repo_path:
            out += "No repo path provided to update"
            return status, out
        if not is_git_repo(self.repo_path):
            out += f"repo path: {self.repo_path} is not a git repository"
            return status, out

        out += f"Updating repository @ {self.repo_path}\n"
        # Get current git repo state
        gp = self.repo_path
        repo = git.Repo(gp)
        git_commit = repo.git.rev_parse(repo.head.commit.hexsha, short=7)
        try:
            git_branch = str(repo.active_branch)
        except TypeError:
            git_branch = None
        try:
            _, git_tag, _ = self.run_gitcmd(
                f"git describe --exact-match {git_commit}", None, True
            )
        except git.exc.GitCommandError:
            git_tag = None
        out += f"Repo at branch: {git_branch} commit: {git_commit} tag: {git_tag}\n"
        out += f"Requested branch: {branch} commit: {commit} tag: {tag}\n"
        # Check if the repo is already in requested state
        if tag:
            if git_tag == tag:
                if logger is not None:
                    out += f"Not updating, repo already at required tag : {tag}"
                    logger.debug(out)
                if ret_out:
                    return True, out
                else:
                    return
        if branch and commit:
            short_sha = repo.git.rev_parse(commit, short=7)
            if (git_branch == branch) and (git_commit == short_sha):
                if logger is not None:
                    out += f"Not updating, repo already at branch {git_branch}, {git_commit}"
                    logger.debug(out)
                if ret_out:
                    return True, out
                else:
                    return
        # Update the repo to user specified state
        status = status or self.run_gitcmd("git remote update -p")
        status = status or self.run_gitcmd("git reset --hard")
        if tag:
            status = status or self.run_gitcmd(f"git checkout {tag}")
            out += f"checked out tag {tag}"
        elif branch:
            status = status or self.run_gitcmd(f"git checkout {branch}")
            status = status or self.run_gitcmd(f"git pull origin {branch}")
            out += f"updated branch: {repo.active_branch}"
            if commit:
                status = status or self.run_gitcmd(f"git checkout {commit}")
                out += f" checked out commit {commit}"
        else:  # No tag/branch provided, update to latest master branch
            status = status or self.run_gitcmd("git checkout master")
            status = status or self.run_gitcmd("git pull origin master")
            commit = repo.git.rev_parse(repo.head.commit.hexsha, short=7)
            out += f"updated to master branch, commit {commit}"
        if logger is not None:
            logger.debug(out)
        if ret_out:
            return not status, out
        return not status

    def log(self):
        if self.logfile is None:
            return
        # repo_url = self.repo.git.remote("get-url", "origin")
        # FIXME due to git version not supporting the command (Required git version 2.23.0)
        repo_url = self.repo.git.config("--get", "remote.origin.url")
        repo_branch = self.repo.git.branch()

        with open(self.logfile, "w") as f:
            f.write("\n******************************************************\n")
            f.write(f" REPO URL: {repo_url}\n")
            f.write(f" BRANCH: {repo_branch}\n")
            f.write(f" ORIGIN_COMMIT: {self.origin_commit}\n")

            commit_diff = self.repo.git.log(
                f"{self.last_hash}..HEAD", "--pretty=format:%H - %an, %ar : %s"
            )
            if commit_diff:
                commit_diff = commit_diff.split("\n")
                f.write(" COMMIT DIFF:\n")
                for line in commit_diff:
                    f.write(f"\t{line}\n")
            f.write("\n******************************************************\n")


def is_git_repo(repo_path):
    """Checks if a given path is a git repo

    Args:
        repo_path (os.path): path to the dir that needs to be tested to see if the dir is a git repo

    Returns:
        bool: True if path is a git repo.
    """

    try:
        _ = git.Repo(repo_path).git_dir
        return True
    except git.exc.InvalidGitRepositoryError:
        return False


def clone(git_params, repo_path, logfile, workDir=None, clone_once=False, **kwargs):

    git = Git(git_params, repo_path, clone_once, logfile)

    git.clone(**kwargs)

    if git.repo_cloned:

        git.checkout()

        git.apply_patch(workDir)

        git.log()


def surround_double_quotes(string: str) -> str:
    """Surrounds the input string with double quotes and returns the modified string.

    Args:
        string: String to be modified.

    Returns:
        str: String with double quotes.
    """

    return '"' + str(string) + '"'


def print_err_exit(err_msg: str) -> None:
    """Print the Error Message and Exits the Program.

    Args:
        err_msg: Error Message.
    """

    print("ERROR: " + err_msg)

    sys.exit(1)


def print_warn(warn_msg: str) -> None:
    """Print the Warning Message and continues the Program execution.

    Args:
        warn_msg: Warning Message.
    """
    print("WARNING: " + warn_msg)


def print_msg(msg: str) -> None:
    """Print * across the screen width and puts the msg in the center of the screen.

    Args:
        msg: Message to be print.
    """
    try:
        rows, columns = os.popen("stty size", "r").read().split()
        print(str(msg).center(int(columns), "*"))
    except:
        print(str(msg))


def is_var_type(var: Any, expected_type: Any) -> bool:
    """Returns True if the expected variable type and provided variable type matches

    Args:
        var: Any valid python variable.
        expected_type: Any valid python variable type.

    Returns:
        bool: Returns True, else Exits the Program.
    """

    if not (type(var) == expected_type):
        msg = "Expected:" + str(expected_type) + " " + "Received:" + str(type(var))
        print_err_exit(msg)
    return True


def stripper(elements_list: List[str]) -> List[str]:
    """Strips unwanted spaces from start and end, in a list of strings.

    Args:
        elements_list: List of strings.

    Returns:
        :obj:`list` of :obj:`str`: Stripped strings list.
    """
    is_var_type(elements_list, list)
    return [element.strip() for element in elements_list]


def is_defined(args, mandatory_args):
    """Checks if the argparser.args contains all the mandatory args, Else report error and exit.

    Args:
        args (:obj:`ArgParser.args`): Argparser args.
        mandatory_args: Mandatory args.
    """

    # Test for the mandatory args
    for arg in mandatory_args:
        if arg not in args.keys() or args[arg] is None or args[arg] == "":
            msg = surround_double_quotes(arg) + " " + "is not defined"
            print_err_exit(msg)


def del_element(
    element: str, elements_list: List[str], silent_discard: bool = True
) -> None:
    """Removes an element from a list.

    Args:
        element: Element to be removed.
        elements_list: List of Strings.
        silent_discard: Discard Message. Defaults to True.
    """

    is_var_type(elements_list, list)

    try:
        elements_list.remove(element)
    except:
        if not silent_discard:
            msg = (
                "KeyError:" + " " + surround_double_quotes(element) + " " + "not found"
            )
            print_err_exit(msg)


def write_to_yaml(data: str, filepath: str, silent_discard: bool = True) -> None:
    """Write the data to YAML file, raises Error Message on demand.

    Args:
        data: Data to be written.
        filepath: Path of file.
        silent_discard: Discard Message. Defaults to True.
    """

    is_successful = False
    try:
        with open(filepath, "w") as outfile:
            yaml.dump(data, outfile, default_flow_style=False)
            is_successful = True
    except:
        pass
    if not silent_discard:
        if is_successful:
            print("Write Data to file: %s is successful" % filepath)
        else:
            msg = (
                "Write Data to file:"
                + " "
                + surround_double_quotes(filepath)
                + " "
                + "failed"
            )
            print_err_exit(msg)


def del_key(key: str, dictionary: dict, silent_discard: bool = True) -> None:
    """Deletes Key from a dictionary, and raises Not Found Error Message on demand.

    Args:
        key: Key to be deleted.
        dictionary: Dictionary.
        silent_discard: Discard Message. Defaults to True.
    """

    is_var_type(dictionary, dict)

    try:
        del dictionary[key]
    except:
        if not silent_discard:
            msg = "KeyError:" + " " + surround_double_quotes(key) + " " + "not found"
            print_err_exit(msg)


def get_env(env_var_list: List) -> dict:
    """Return dictionary of the env variables Else raises Error Message.

    Args:
        env_var_list: List of the variables expected to be present in environment.

    Returns:
        dict: Environment variables.
    """

    is_var_type(env_var_list, list)

    if len(env_var_list) <= 0:
        msg = "Empty env_var_list"
        print_err_exit(msg)

    vars_dict = {}
    for var in env_var_list:
        if os.environ.get(var) is None:
            msg = (
                "ENV_VAR:" + " " + surround_double_quotes(var) + " " + "is not defined"
            )
            print_err_exit(msg)
        else:
            vars_dict[var] = os.environ.get(var)
    return vars_dict


def is_file(filepath: str, silent_discard: bool = True) -> bool:
    """Return True if the file exists Else returns False and raises Not Found Error Message.

    Args:
        filepath: File Path.

    Raises:
        OSError: Raises OSError exception if file not found.

    Returns:
        bool: True, if file is found Or False, if file is not found.
    """

    try:
        if os.path.isfile(filepath):
            return True
        else:
            raise OSError
    except:
        if not silent_discard:
            print("%s No such file exists" % filepath)
        return False


def is_dir(dirpath: str, silent_discard: bool = True) -> bool:
    """Return True if the folder exists Else returns False and raises Not Found Error Message.

    Args:
        dirpath: Folder Path.

    Raises:
        OSError: Raises OSError exception if folder not found.

    Returns:
        bool: True, if folder is found Or False, if folder is not found.
    """

    try:
        if os.path.isdir(dirpath):
            return True
        else:
            raise OSError
    except:
        if not silent_discard:
            print("%s No such directory exists" % dirpath)
        return False


def remove(path: str, silent_discard: bool = True) -> None:
    """Removes any file or folder recursively, if it exists else reports error message based on user demand.

    Args:
        path: Directory or file path.
    """
    is_successful = False
    try:
        if is_dir(path):
            os.sync()
            shutil.rmtree(path)
            is_successful = True
        else:
            os.remove(path)
            is_successful = True
    except OSError as e:
        pass
    if not silent_discard:
        if is_successful:
            print("%s Removed successfully" % path)
        else:
            print("Error: %s" % path, e.strerror)  # FIXME: e doesn't exist here
            sys.exit(1)


def reset(path: str) -> None:
    remove(path)
    mkdir(path)


def load_yaml(filepath: str) -> Optional[dict]:
    """Read yaml file data and returns data in a dict format.

    Args:
        filepath: Path of the yaml file.

    Returns:
        dict: Return Python dict if the file reading is successful.
    """

    if is_file(filepath):
        try:
            with open(filepath) as f:
                data = yaml.safe_load(f)
            return data
        except:
            print("%s file reading failed" % filepath)
            return None
    else:
        return None


def mkdir(folderpath: str, silent_discard: bool = True) -> None:
    """Create the folder structure, raises Error Message on demand.

    Args:
        folderpath: Path of the folder structure.
    """
    is_successful = False
    try:
        os.makedirs(folderpath)
        is_successful = True
    except:
        pass

    if not silent_discard:
        if is_successful:
            print("%s Directory created " % folderpath)
        else:
            print("%s Unable to create directory " % folderpath)
            sys.exit(1)


def mkfile(fname: str, silent_discard: bool = True) -> None:
    """Open an empty file, raises Error Message on demand
       Equivalent to touch in shell

    Arguments:
        filepath {string} -- Path of file
    """
    is_successful = False
    try:
        Path(fname).touch()
        is_successful = True
    except:
        pass
    if not silent_discard:
        if is_successful:
            print("%s Created File" % fname)
        else:
            print("%s Unable to create file " % fname)
            sys.exit(1)


def is_error(stderr_msg: str) -> bool:
    """Return True if the error string not found else exits with error message.

    Args:
        stderr_msg: std error message.
    """
    err_list = ["fatal", "error", "Error:"]

    for err in err_list:
        if err in stderr_msg:
            print_err_exit(stderr_msg)
    return True


def detailed_error():
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)


def copy_file(src: str, dest, follow_symlinks=False):
    is_file(src)
    shutil.copy2(src, dest, follow_symlinks=follow_symlinks)


def cp_all_files(
    src: str, dest: str, symlinks: bool = False, ignore: bool = None
) -> None:
    if is_dir(src, False) == True:
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dest, item)
            if os.path.isfile(s):
                shutil.copy2(s, d)


def copyDirectory(src: str, dst: str, symlinks: bool = False, ignore=None) -> None:
    if not is_dir(dst):
        mkdir(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if is_dir(s):
            if is_dir(d):
                copy_tree(s, d, symlinks)
            else:
                shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


# Read file matching regex lines only
def read_file(file_path, regex):
    valid_lines = []
    with open(os.path.expandvars(file_path), "r") as stream:
        line = stream.readline()
        while line:
            line = str(line).strip("\n")
            # FIX # Support
            e = re.search(regex, line)
            if e:
                e = e.string.split(regex)[1].strip(" ")
                e = os.path.expandvars(e)
                valid_lines.append(str(e))
            line = stream.readline()
    return valid_lines


def export_env(file_path: str) -> None:
    for line in read_file(file_path, "export"):
        # FIXME: Check for #/commented one to not to export it.
        (key, _, value) = line.partition("=")
        value = os.path.expandvars(value).strip('"')
        # FIXME: Check for valid substituion
        os.environ[key] = value


def init_conf(file_path="${ROOT}/conf/init.conf", regex="source"):
    data = read_file(file_path, regex)
    for e in data:
        e = os.path.expandvars(e)


class LoadFromFile(argparse.Action):
    """Allows to read from a yaml file and using argparse to set the attribute values.

    Args:
        argparse (:obj:`Namespace`): It reads the user arguments from the file using argparse library.

    Raises:
        CustomError: Raises Custom error message if file reading fails.
    """

    def __call__(self, parser, namespace, values, option_string=None):

        # Read user config file
        try:
            with values as f:
                contents = f.read()
            data = yaml.safe_load(contents)

            # Set the arguments after reading from the file. It will stop reading after one correct read
            for k, v in data.items():
                for nk, nv in v.items():
                    setattr(namespace, nk, nv)
                break
        except Exception as e:
            detailed_error()


def runcmd(cmd, logfile=None) -> bool:

    ret = True
    if logfile is None:
        try:
            subprocess.check_call(cmd, shell=True)
        except subprocess.CalledProcessError:
            ret = False
    else:
        try:
            subprocess.check_call(cmd, shell=True, stdout=logfile, stderr=logfile)
        except subprocess.CalledProcessError:
            ret = False
    return ret


def check_output(cmd, env=None, silent_discard=False):
    try:
        output = subprocess.check_output(
            cmd, env=env, shell=True, universal_newlines=True, stderr=subprocess.PIPE
        )
        returncode = 0
    except subprocess.CalledProcessError as e:
        err_msg = f'"{cmd}" failed with {e.returncode}'
        if not silent_discard:
            print(err_msg, file=sys.stderr)
            raise Exception(err_msg) from None
        else:
            print(err_msg)
        output = None
        returncode = e.returncode
    return output, returncode


def runcmd_p(cmd, log, env=None, cwd="./", expected_code=0, return_code=False):
    """Sends command on to the console and raises assertion error if the
    command is not executed successfully.

    Args:
        cmd (str): Command to be executed.
        log (logger): logger to record debug prints
        cwd (str): PWD path to execute cmd
        expected_code (int): Expected return code value from the function
        return_code (boolean): True = returns cmd exit code, False = Asserts error
    Raises:
        Assertion error only when command execution fails
    """
    log.debug(f"cmd: {cmd}")
    # FIXME: stderror will also get into stdout.
    # Needed to find a way to seperate them.
    with subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        env=env,
        cwd=cwd,
        encoding="utf-8",
        shell=True,
        bufsize=1,
    ) as p:
        for line in p.stdout:  # b'\n'-separated lines
            log.debug(line)
    retcode = p.wait()
    if retcode != expected_code:
        err_msg = f"{cmd} failed with return code {retcode}, expected {expected_code}"
        log.error(err_msg)
        if return_code:
            return retcode
        else:
            assert False, err_msg
    elif return_code:
        return retcode


# Function to add newline in file.
def add_newline(File, newline):
    with open(File, "a") as fd:
        fd.write(newline + "\n")


# Function to remove line with matched string
def remove_line(File, match_string) -> None:
    with open(File, "r+") as f:
        new_f = f.readlines()
        f.seek(0)
        for line in new_f:
            if match_string not in line:
                f.write(line)
        f.truncate()


# Function to replace string.
def replace_string(File, search_string: str, replace_string: str) -> None:
    if is_file(File) == True:
        with open(File, "r+") as fd:
            filedata = fd.read()
            filedata = re.sub(search_string, replace_string, filedata)
            fd.seek(0)
            fd.write(filedata)
            fd.truncate()
    else:
        raise Exception(f"Error: {File} file not found")


# Function to replace line if match string found.
def replace_line(File: str, search_string: str, add_line: str) -> None:
    if is_file(File) == True:
        add_line = add_line + "\n"
        with fileinput.input(File, inplace=True) as fd:
            for line in fd:
                if search_string in line:
                    line = add_line
                sys.stdout.write(line)
    else:
        raise Exception(f"Error: {File} file not found")


def git_clone(
    repo_url, clone_path, repo_branch, rev=None, sparse_checkout_path=[], **kwargs
):
    """Allows to clone git repo with submodules

    Args:
        repo_url: git repo url.
        clone_path: path to clone repo with some name
        repo_branch: git repo branch

    Raises:
        Error: Raises error when failed to clone repo.
    """

    try:
        no_checkout = True if len(sparse_checkout_path) else False
        git.Repo.clone_from(
            repo_url, clone_path, branch=repo_branch, no_checkout=no_checkout, **kwargs
        )
        repo = git.Repo(clone_path)
        if len(sparse_checkout_path):
            with repo.config_writer() as cw:
                cw.set_value("core", "sparseCheckout", "true")
            checkout_path = os.path.join(clone_path, ".git/info/sparse-checkout")
            with open(checkout_path, "w") as fd:
                fd.writelines(sparse_checkout_path)
            repo.git.checkout(repo_branch)

        for submodule in repo.submodules:
            submodule.update(init=True)
            sub_repo = submodule.module()
            sub_repo.git.pull()
        if rev:
            repo.git.checkout(rev)
        print(f"Info: {repo_url} Cloned successfully")
        return True
    except Exception as e:
        print(f"Error: Failed to clone {repo_url}")
        raise Exception(f"Error: Failed to clone {repo_url}")


def has_key(dict_name, key) -> bool:
    """To check if key available in dictionary
    And checks if key is None

    Args:
       dict_name: Dictionary name
       key: Key name
    """
    if isinstance(key, str) and "." in key:
        key = key.split(".")
    else:
        first, rest = key, None

    if isinstance(key, list):
        first, rest = key[0], key[1:]

    if rest:
        return has_key(dict_name[first], rest)
    else:
        if first in dict_name:
            if dict_name[first]:
                return True
            else:
                return False
        else:
            return False


def get_var(config, key: str, raise_except: bool = False) -> Any:
    """This api returns vale of key in config.
    If key is not present, it will return False if raise_except is False.
    else it will raise exception.

    Args:
        config: Configuration from test case
        key: key for which value needed to be returned
        raise_except: if key is not found in config, returning False or Raising
                      exception depends on this flag.

    Returns:
        string: if key is present
    """

    warn(
        "get_var is deprecated; use dictionary .get() method instead.",
        category=DeprecationWarning,
    )

    if not has_key(config, key):
        if raise_except:
            raise Exception(f"Error: Key not found!")
        else:
            return None
    else:
        if isinstance(key, str) and "." in key:
            key = key.split(".")
        else:
            first, rest = key, None

        if isinstance(key, list):
            first, rest = key[0], key[1:]
        if rest:
            # if rest is not empty, run the function recursively
            return get_var(config[first], rest)
        else:
            return config[first]


def set_var(config, key, value):

    if isinstance(key, str) and "." in key:
        keys = key.split(".")
        tree_dict = value
        for ikey in reversed(keys):
            tree_dict = {ikey: tree_dict}
    else:
        tree_dict = {key: value}

    dict_update(config, tree_dict)


def isvalid_config(config, key, default, valid_list, logger=None):
    """Function that checks if a value for key exist in config and if it doesnt
    exist uses the default value, and see if the value/default exists in the valid_list

    Args:
        config (dict): config object
        key (str): key to used to get value from config
        default (str): default value to be assigned if not value exist for key
        valid_list (list): list of valid choices for key
        logger (logger.getlogger): log the error output. Defaults to None.

    Returns:
        value/False: returns the valid value or False
    """
    val = config.get(key, default)
    if val in valid_list:
        return val
    else:
        if logger is not None:
            logger.error(
                f"User input {key} = {val} is invalid!\n" f"Use values in: {valid_list}"
            )
        return False


def convert_list(*argv):
    """This api takes list/strings and
    returns list
    """
    ret_list = []
    for arg in argv:
        if arg:
            if type(arg) == list:
                ret_list += arg
            else:
                ret_list += [arg]

    return ret_list


def remove_all_files(file_path: str) -> None:
    import glob

    """ This api removes all files under directory
    """
    files = glob.glob(f"{file_path}/*")
    for f in files:
        os.remove(f)


def symlink(src_file: str, dst_file: str) -> None:
    """This api is to symlink file or directory."""
    print(os.getcwd())
    if os.path.islink(src_file):
        os.unlink(src_file)
    else:
        remove(src_file)
    if not is_file(dst_file) or is_dir(dst_file):
        raise Exception(f"Error: {dst_file} file or directory not found to symlink")
    os.symlink(dst_file, src_file)


def get_relpath_tcrepo(fpath):
    """This api takes file path and returns
    relative path with reference to tcRepo/ dir
    """
    # File relative path
    frpath = os.path.relpath(fpath, f"{os.environ.get('ROOT')}/tcRepo")
    return "/".join([i for i in frpath.split("/") if i])  # Filter out empty elements


def get_test_path_list(fpath):
    """This api takes full path of test dir and splits into list.
    It will have list after tcRepo onwards.
    """
    fpath = get_relpath_tcrepo(fpath)
    fpath_list = fpath.split("/")
    return [x for x in fpath_list if x]  # Filter out empty values


def get_base_name(fpath):
    """This api takes rel path or full path and returns
    base name"""
    return os.path.basename(fpath)


def get_dir_name(fpath):
    """This api takes file path and returns it's directory
    path"""
    return os.path.dirname(fpath)


def get_dirs(fpath: str, exclude_dirs="") -> List:
    """This api takes path and exclude dirs list,
    returns list of dirs available in provided path
    by default it exclude dirs which startswith ('.', '__')
    """

    dirs = [
        str(dirs).strip("./")
        for dirs in os.listdir(fpath)
        if is_dir(os.path.join(fpath, dirs))
        and dirs not in exclude_dirs
        and not dirs.startswith((".", "__"))
    ]
    return dirs


def get_files(directory, extension=None, filename=None, basename=False, abs_path=False):
    """This api takes directory path and
    returns list of files with the given extension or returns list of files
    with same file name and different extension
    """
    files = []
    for f in os.listdir(directory):
        if extension is None and filename:
            if f.startswith(filename + "."):
                files += [f]
        elif f.endswith("." + extension):
            if basename:
                files += [str(f).replace(f".{extension}", "")]
            else:
                files += [f]

    if abs_path:
        abs_files = []
        for f in files:
            abs_files += [get_abs_path(f"{directory}/{f}")]
        return abs_files

    return files


def get_abs_path(fpath):
    """This api takes file path and returns it's absolute
    path"""
    return os.path.abspath(fpath)


def get_original_path(fpath):
    """This api takes file path and returns it's original
    path. It is equivalent to readlink"""
    return os.path.realpath(fpath)


def overrides(conf, var):
    """ This api overrides the dictionary which contains same key's """
    if has_key(conf, var):
        for key, value in conf[var].items():
            conf[key] = value
    return conf


def find_file(search_file: str, search_path: str):
    """This api find the file in sub-directories and returns
    absolute path of file, if file exists"""
    for File in Path(search_path).glob(f"**/{search_file}"):
        return File


def get_test_params(mydict, keys=[]):
    """This api converts a dict of lists into combinations
    keys and values. This can be used for dicts with
    any number of levels"""
    lists = []
    if type(mydict) is not dict:
        tmp = []
        if type(mydict) is str:
            tmp += [keys + [mydict]]
        else:
            for item in mydict:
                tmp += [keys + [item]]
        return tmp

    for (key, values) in mydict.items():
        if type(key) is tuple:
            for item in key:
                lists += get_test_params(values, keys + [item])
        else:
            lists += get_test_params(values, keys + [key])

    return lists


def check_if_string_in_file(file_name: str, string_to_search: str) -> bool:
    """ Check if any line in the file contains given string """
    with open(file_name, "r") as read_obj:
        for line in read_obj:
            if re.search(string_to_search, line):
                return True
    return False


def random_string(string_length=8):
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(string_length))


def get_combinations(args):
    for i, arg in enumerate(args):
        if isinstance(arg, str):
            args[i] = [arg]
        elif arg is None:
            args[i] = [arg]
        elif arg == []:
            args[i] = [None]
    return itertools.product(*args)


def flatten_nested_items(dictionary):
    """Flatten a nested_dict.  iterate through nested dictionary
    (with iterkeys() method) and return with nested keys
    flattened into a tuple"""
    if sys.hexversion < 0x03000000:
        keys = dictionary.iterkeys
        keystr = "iterkeys"
    else:
        keys = dictionary.keys
        keystr = "keys"
    for key in keys():
        value = dictionary[key]
        if hasattr(value, keystr):
            for keykey, value in flatten_nested_items(value):
                yield (key,) + keykey, value
        else:
            yield (key,), value


def get_flattened_dict(dictionary, remove_element=None):
    """This api converts a given nested dictionary into
    a flattened one, by converting all the nested keys into
    combinations of tuple keys.

    For Example:
    mydict = {}
    mydict['a']['b'] = 1
    mydict['a']['b']['c'] = 2

    output = get_flattened_dict(mydict)

    output
    {
    ('a', 'b') = 1,
    ('a', 'b', 'c') = 2
    }
    """
    flattened_dict = flatten_nested_items(dictionary)
    mydict = {}
    for key, val in flattened_dict:
        if remove_element in key and remove_element:
            key = list(key)
            key.remove(remove_element)
            key = tuple(key)
        mydict[key] = val
    return mydict


def dict_update(d, *src):
    for u in src:
        for k, v in u.items():
            if isinstance(v, collections.abc.Mapping):
                d[k] = dict_update(d.get(k, {}), v)
            else:
                d[k] = v
    return d


def filter_dict(mydict, scenario_list):
    """This api filters dictionary based on given scenario list. The scenarios in
    the given list are again a list of keys that has to be checked with the
    flattened tuple keys of a nested dict.
    """
    filtered_set = set()
    flat_dict = get_flattened_dict(mydict)
    for scenario in scenario_list:
        scenario = set(scenario)
        for key, val in flat_dict.items():
            key = set(key)
            if scenario.issubset(key):
                filtered_set.update(set(val))
    return list(filtered_set)


def filter_keys(keys):
    """This api is used to take a string or a list of one string and split it
    appropriately to get the list of keys to look for while filtering a
    dictionary. It is first split on basis of semicolon(;) which acts like a
    separator of scenarios given. Next it's split on comma which is the list
    of keys that the scenario mean.
    """

    if keys is None:
        filtered_keys = [[]]
    else:
        if isinstance(keys, str):
            keys = [keys]
        filtered_list = keys[0].split(";")
        filtered_keys = [val.split(",") for val in filtered_list]

    return filtered_keys


def get_config_data(config, key, temp=None):
    if temp is None:
        temp = config
    if isinstance(key, str) and "." in key:
        key = key.split(".")
    else:
        first, rest = key, None

    if isinstance(key, list):
        first, rest = key[0], key[1:]
    if rest:
        # if rest is not empty, run the function recursively
        return get_config_data(config, rest, temp[first])
    else:
        temp_dict = dict(temp)
        return parse_config(config, temp_dict[first])


def parse_config(config, value):
    """ Parse config for string interpolation"""

    config["tmp_value"] = value
    return config["tmp_value"]


def colorstr_to_plainstr(string):
    """ Conversion from colour string to plain string if any"""
    ansi_escape = re.compile(r"\x1b(\[.*?[@-~]|\].*?(\x07|\x1b\\))")
    format_string = ansi_escape.sub("", str(string))
    return format_string


class FileAdapter:
    def __init__(self, logger):
        self.logger = logger
        self._data = ""
        atexit.register(self.exit)

    def write(self, data):
        # NOTE: data can be a partial line, multiple lines
        self._data += data
        lines = re.findall(".*\n", self._data, re.M)  # find lines
        for line in lines:
            self.logger.debug(line.strip())
            self._data = self._data.replace(line, "")

    def flush(self):
        pass  # leave it to logging to flush properly

    def exit(self):
        self.logger.debug(self._data)
