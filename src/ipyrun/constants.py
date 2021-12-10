import pathlib

PATH_PACKAGE = pathlib.Path(__file__).parent
PATH_RUNAPP_HELP = PATH_PACKAGE / 'images' / 'RunApp.png'
PATH_RUNAPPS_HELP = PATH_PACKAGE / 'images' / 'RunBatch.png'

JOBNO_DEFAULT = 'J5001' #  testing job

BUTTON_WIDTH_MIN = '41px'
BUTTON_WIDTH_MEDIUM = '90px'
BUTTON_HEIGHT_MIN = '25px'

FPTH_MXF_ICON = PATH_PACKAGE / 'images' / 'mxf-icon.png'
FPTH_USER_ICON = PATH_PACKAGE / 'images' / 'user-icon.png'
FPTH_TEMPLATE_PROCESSES = PATH_PACKAGE / 'processes-schedule.csv'

def load_test_constants():
    """only in use for debugging within the package. not used in production code.

    Returns:
        module: test_constants object
    """
    from importlib.machinery import SourceFileLoader
    path_testing_constants = PATH_PACKAGE.parents[1] / 'tests' / 'constants.py'
    test_constants = SourceFileLoader("constants", str(path_testing_constants)).load_module()
    return test_constants