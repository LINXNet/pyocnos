#!/usr/bin/env python
""" Python library to remotely manage/automate
 switches running OcNOS operating system. """

from setuptools import setup, find_packages

with open('requirements.txt', 'r') as requirements:
    install_requires = [line.strip() for line in requirements if line and not line.startswith('#')]

version = '0.5.20'
setup(
    name='pyocnos',
    version=version,
    py_modules=['pyocnos'],
    packages=find_packages(),
    install_requires=install_requires,
    include_package_data=True,
    description='Python API to interact with network devices running OcNOS',
    author='LINX',
    author_email='developers@linx.net',
    url='https://github.com/LINXNet/pyocnos/',
    download_url='https://github.com/LINXNet/pyocnos/tarball/%s' % version,
    keywords=['OcNOS', 'networking'],
    classifiers=[
         'Programming Language :: Python :: 3'
     ],
    python_requires='~=3.0',
    entry_points={
        'console_scripts': ['pyocnos=pyocnos.command_line:main'],
    }
)
