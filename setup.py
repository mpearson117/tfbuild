import os
from setuptools import setup

with open("README.md", "r") as readme_fd:
    long_description = readme_fd.read()

setup(
    name="tfbuild",
    setup_requires=['setuptools-git-versioning'],
    setuptools_git_versioning={
        "template": "{tag}",
        "dev_template": "{tag}",
        "dirty_template": "{tag}",
        },
    author="Michael Pearson",
    description="TFBuild is a command line tool for Terraform ",
    url="https://github.com/mpearson117/tfbuild",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=['tfbuild'],
    package_dir={"": "src"},
    install_requires=[
        "boto3",
        "colorlog",
        "confuse",
        "GitPython", 
        "jsonpickle", 
        "py_console",
        "PyYAML", 
        "pyhcl", 
        "schematics>=2.0,<3.0", 
        "six>=1.11,<2"
        ],
    extras_require={
        'dev:python_version > "3"': ["pytest>=5.0,<6",],
        "dev": {"pytest-cov", "pytest-mock", "codecov"},
    },
    entry_points={"console_scripts": ["tfbuild = tfbuild.cli:main","tfb = tfbuild.cli:main",],},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Pre-processors",
        "Topic :: System :: Systems Administration",
    ],
)
