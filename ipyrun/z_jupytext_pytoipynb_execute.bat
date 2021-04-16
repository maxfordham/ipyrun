pushd %~dp0
@echo off 
call conda activate mf_base

echo -----------------------------------------
echo Jupytext: Convert py files to ipynb files
echo -----------------------------------------
echo https://github.com/mwouts/jupytext/blob/master/docs/using-cli.md
echo this allows the .py representations of the notebook files only
echo to be stored on Git (easy diff's and version control), running  
echo this script can regenerate notebook files from the percent scripts. 
echo -----------------------------------------

set "UserInput=all"
set /p "UserInput=Enter path of file to convert of or just ENTER to convert all[%UserInput%] : "
echo jupytext convert: %UserInput%

if %UserInput%=="all" (
	call jupytext --set-formats ipynb,py --execute _filecontroller.py
	call jupytext --set-formats ipynb,py --execute _ipydisplayfile.py
	call jupytext --set-formats ipynb,py --execute _ipyeditcsv.py
	call jupytext --set-formats ipynb,py --execute _ipyeditjson.py
	call jupytext --set-formats ipynb,py --execute _runconfig.py
	call jupytext --set-formats ipynb,py --execute ipyrun.py
	call jupytext --set-formats ipynb,py --execute ipyrun_archived.py
	call jupytext --set-formats ipynb,py --execute ipyrun_overheating.py
) else (
    call jupytext --set-formats ipynb,py --execute %UserInput%
)

pause