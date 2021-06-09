# ipyrun

ipyrun is designed for rapidly creating an app user interface (to be operated in a jupyter notebook / lab or voila app) to run a script or process and generate resultant output files. The app caches input, output and runtime data, such that the previous state of the app is available to the user when returning. C

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
conda install -c file:///mnt/conda-bld ipyrun
```

- install pip dependencies

```bash
pip install mydocstring ipyaggrid
```

- install pip dependencies

jupyter labextension install @jupyter-widgets/jupyterlab-manager
jupyter labextension install jupyterlab-plotly
jupyter labextension install plotlywidget
jupyter labextension install ipyaggrid
jupyter labextension install ipysheet
jupyter labextension install @jupyter-widgets/jupyterlab-manager
jupyter lab build

## Build

- [conda-bld](docs/conda-bld.md)
