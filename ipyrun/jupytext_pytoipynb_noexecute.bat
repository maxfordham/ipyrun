pushd %~dp0
::  https://github.com/mwouts/jupytext/blob/master/docs/using-cli.md
call conda activate mf_base
call jupytext --set-formats ipynb,py _filecontroller.py
call jupytext --set-formats ipynb,py _ipydisplayfile.py
call jupytext --set-formats ipynb,py _ipyeditcsv.py
call jupytext --set-formats ipynb,py _ipyeditjson.py
call jupytext --set-formats ipynb,py _runconfig.py
call jupytext --set-formats ipynb,py ipyrun.py
call jupytext --set-formats ipynb,py ipyrun_archived.py
call jupytext --set-formats ipynb,py ipyrun_overheating.py
pause