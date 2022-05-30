#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages
import versioneer


def diff(li1, li2): 
    '''find the difference between 2 lists'''
    return [i for i in li1 + li2 if i not in li1 or i not in li2]  

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('requirements.txt') as requirements_file:
    requirements = requirements_file.readlines()
requirements = [r.split('==')[0] for r in requirements]
piponly = ['mydocstring']
requirements = diff(requirements, piponly)


setup(
    name='ipyrun',
    author="John Gunstone",
    author_email='gunstone.john@gmail.com',
    description="A generic user interface for running scripts. Data inputs to scripts are defined by standard datafiles (e.g. csv, json), and data files are generated as outputs when the script is run. A timestamped record of script execution is maintained. An ipywdiget user interface allows users to edit script input data and view outputs of script execution.",
    license="MIT license",
    long_description=readme,
    long_description_content_type="text/markdown",
    packages=find_packages('src'),
    install_requires=requirements,
    package_dir={'': 'src'},
    url='https://github.com/gunstonej/ipyrun',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    keywords='ipyrun',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.9',
    ]
)
