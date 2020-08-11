pushd %~dp0
call conda activate mf_main
voila 20_RW_OverheatingToolbox.ipynb --static VOILA.STATIC_ROOT
cmd \k