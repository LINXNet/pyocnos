#!/usr/bin/env python
""" Python library to remotely manage/automate
 switches running OcNOS operating system. """

from setuptools import setup, find_packages
from pip.req import parse_requirements
import uuid

install_requirements = parse_requirements(
    'requirements.txt', session=uuid.uuid1()
)

requirements = [str(ir.req) for ir in install_requirements]
version = '0.2.1'

setup(
    name='pyocnos',
    version=version,
    py_modules=['pyocnos'],
    packages=find_packages(),
    install_requires=requirements,
    include_package_data=True,
    description='Python API to interact with network devices running OcNOS',
    author='LINX',
    author_email='developers@linx.net',
    url='https://github.com/LINXNet/pyocnos/',
    download_url='https://github.com/LINXNet/pyocnos/tarball/%s' % version,
    keywords=['OcNOS', 'networking'],
    classifiers=[],
    entry_points={
        'console_scripts': ['pyocnos=pyocnos.command_line:main'],
    }
)
