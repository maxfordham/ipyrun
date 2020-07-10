#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [ ]

setup_requirements = [ ]

test_requirements = [ ]

setup(
    author="John Gunstone",
    author_email='gunstone.john@gmail.com',
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="A generic user interface for running scripts. Data inputs to scripts are defined by standard datafiles (e.g. csv, json), and data files are generated as outputs when the script is run. A timestamped record of script execution is maintained. An ipywdiget user interface allows users to edit script input data and view outputs of script execution.",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='ipyrun',
    name='ipyrun',
    packages=find_packages(include=['ipyrun', 'ipyrun.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/gunstonej/ipyrun',
    version='0.1.0',
    zip_safe=False,
)