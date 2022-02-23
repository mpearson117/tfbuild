import os
from setuptools import setup

#with open("VERSION", "r") as version_fd:
#    VERSION = version_fd.read().strip()

with open("README.md", "r") as readme_fd:
    long_description = readme_fd.read()


setup(
    name="tfbuild",
    version="1.0.0",
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
        "Intended Audience :: IAC Developers",
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