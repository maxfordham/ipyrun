pushd %~dp0
@echo off 
call conda activate mf_base

echo -----------------------------------------
echo Delete Notebooks
echo -----------------------------------------
echo they can be created again using:
echo jupytext_pytoipynb_noexecute.bat
echo or
echo jupytext_pytoipynb_execute.bat

del _filecontroller.ipynb
del _ipydisplayfile.ipynb
del _ipyeditcsv.ipynb
del _ipyeditjson.ipynb
del _runconfig.ipynb
del ipyrun.ipynb
del ipyrun_archived.ipynb
del ipyrun_overheating.ipynb
@RD /S /Q ".ipynb_checkpoints"
pause