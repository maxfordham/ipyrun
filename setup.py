#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages
import versioneer

#  from mf_modules.pydtype_operations import diff
def diff(li1, li2): 
    '''find the difference between 2 lists'''
    return [i for i in li1 + li2 if i not in li1 or i not in li2]  

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('requirements.txt') as requirements_file:
    requirements = requirements_file.readlines()
requirements = [r.split('==')[0] for r in requirements] #  flexible requirements
piponly = ['ipyaggrid']
requirements = diff(requirements, piponly)

#setup_requirements = [ ]
#test_requirements = [ ]

setup(author="John Gunstone",
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
    license="MIT license",
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords='ipyrun',
    name='ipyrun',
    packages=find_packages(include=['ipyrun', 'ipyrun.*']),
    install_requires=requirements,
    #entry_points={'console_scripts': ['mfom=ipyrun.cli:main']},
    #package_dir={'ipyrun':'ipyrun'},
    #include_package_data=True,
    #setup_requires=setup_requirements,
    #test_suite='tests',
    #tests_require=test_requirements,
    url='https://github.com/gunstonej/ipyrun',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
)
