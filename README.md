# ipyrun

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/maxfordham/ipyrun/HEAD)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

![](docs/images/logo.svg)

ipyrun is UI first package built on ipywidgets designed for rapidly creating an app user interface for use in a jupyter notebook / lab or voila app. To run a script or process and generate resultant output files. The app caches input, output and runtime data, such that the previous state of the app is available to the user when returning. 

## Use cases

A generic user interface for running scripts.
Data inputs to scripts are defined by standard datafiles (e.g. csv, json), and data files are generated as outputs when the script is run.
A timestamped record of script execution is maintained.
An ipywdiget user interface allows users to edit script input data and view outputs of script execution.

## Install

- install from network channel

```bash
conda config --add channels file:///mnt/conda-bld
mamba install ipyrun
# or 
mamba install -c file:///mnt/conda-bld ipyrun
```

- install pip dependencies

```bash
pip install mydocstring
```

## Build

- [conda-bld](docs/conda-bld.md)
