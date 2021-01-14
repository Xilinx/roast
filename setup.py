#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from setuptools import setup, find_packages, find_namespace_packages
import codecs
import os

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    with codecs.open(os.path.join(here, *parts), "r") as fp:
        return fp.read()


long_description = read("README.md")
packages = find_packages(exclude=["contrib", "docs", "tests"])
packages.extend(
    find_namespace_packages(include=["roast.*"], exclude=["contrib", "docs", "tests"])
)

setup(
    name="roast",
    version="2.0.0",
    description="Randomized Okaying Across System Topologies (ROAST) Python Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Xilinx/roast",
    author="Ching-Hwa Yu",
    author_email="chinghwa@xilinx.com",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
    ],
    keywords="roast",
    license="MIT",
    packages=packages,
    package_data={"": ["*.yaml", "*.tcl"]},
    python_requires=">=3.6, <4",
    install_requires=[
        "python-configuration[yaml,toml]>=0.8",
        "stevedore>=3.0",
        "gitpython",
        "pexpect",
        "pyyaml",
        "mimesis",
        "filelock",
        "python-box",
    ],
    extras_require={
        "dev": ["pytest", "pytest-mock", "pytest-black", "pytest-freezegun"]
    },
)
