import os

FDIR_PACKAGE = os.path.realpath(os.path.join(os.path.dirname(__file__),'..'))
#  ^ this isn't available in site-packages when built with conda

FDIR_IPYRUN_MAIN = os.path.dirname(__file__)
FPTH_RUNAPP_HELP = os.path.join(FDIR_IPYRUN_MAIN, 'images', 'RunApp.png')
FPTH_RUNAPPS_HELP = os.path.join(FDIR_IPYRUN_MAIN, 'images', 'RunBatch.png')

JOBNO_DEFAULT = 'J5001'

FDIR_ROOT_EXAMPLE = os.path.join(FDIR_PACKAGE,'examples','J0000')
FDIR_APP_EXAMPLE = os.path.join(FDIR_ROOT_EXAMPLE,'test_appdir')
FPTH_SCRIPT_EXAMPLE = os.path.join(FDIR_PACKAGE,'test_scripts','expansion_vessel_sizing.py')
FPTH_SCRIPT_EXAMPLE_CSV = os.path.join(FDIR_PACKAGE,'test_scripts','line_graph.py')


BUTTON_WIDTH_MIN = '41px'
BUTTON_WIDTH_MEDIUM = '90px'
BUTTON_HEIGHT_MIN = '25px'
