import pathlib
import immutables
frozenmap = (
    immutables.Map
)  # https://www.python.org/dev/peps/pep-0603/, https://github.com/MagicStack/immutables

PATH_PACKAGE = pathlib.Path(__file__).parent
PATH_RUNAPP_HELP = PATH_PACKAGE / 'images' / 'RunApp.png'
PATH_RUNAPPS_HELP = PATH_PACKAGE / 'images' / 'RunBatch.png'

JOBNO_DEFAULT = 'J5001' #  testing job

BUTTON_WIDTH_MIN = '41px'
BUTTON_WIDTH_MEDIUM = '90px'
BUTTON_HEIGHT_MIN = '25px'
BUTTON_MIN_SIZE = frozenmap(width=BUTTON_WIDTH_MIN, height=BUTTON_HEIGHT_MIN)

STATUS_BUTTON_UPTODATE = frozenmap(
    icon="fa-check",
    style={},
    button_style="success",
    tooltip="up-to-date",
    layout={"width": BUTTON_WIDTH_MIN, "height": "40px"},
    disabled=True
)

STATUS_BUTTON_NOOUTPUTS = frozenmap(
    icon="fa-circle",
    style={'button_color':'LightYellow'},
    button_style="",
    tooltip="no-outputs",
    layout={"width": BUTTON_WIDTH_MIN, "height": "40px"},
    disabled=True
)

STATUS_BUTTON_NEEDSRERUN = frozenmap(
    icon="fa-refresh",
    style={},
    button_style="danger",
    tooltip="outputs out-of-date. needs re-run",
    layout={"width": BUTTON_WIDTH_MIN, "height": "40px"},
    disabled=True
)
STATUS_BUTTON_ERROR = frozenmap(
    icon="fa-exclamation-triangle",
    style={},
    button_style="danger",
    tooltip="outputs out-of-date. needs re-run",
    layout={"width": BUTTON_WIDTH_MIN, "height": "40px"},
    disabled=True
)

DI_STATUS_MAP = frozenmap(
    up_to_date=STATUS_BUTTON_UPTODATE,
    no_outputs=STATUS_BUTTON_NOOUTPUTS,
    outputs_need_updating=STATUS_BUTTON_NEEDSRERUN,
    error=STATUS_BUTTON_ERROR
)

FPTH_MXF_ICON = PATH_PACKAGE / 'images' / 'mxf-icon.png'
FPTH_USER_ICON = PATH_PACKAGE / 'images' / 'user-icon.png'
FPTH_TEMPLATE_PROCESSES = PATH_PACKAGE / 'processes-schedule.csv'
FNM_CONFIG_FILE = "config-shell_handler.json"

def load_test_constants():
    """only in use for debugging within the package. not used in production code.

    Returns:
        module: test_constants object
        
    Example:
        DIR_TESTS
        DIR_EXAMPLE_PROCESS
        DIR_EXAMPLE_BATCH
    """
    from importlib.machinery import SourceFileLoader
    path_testing_constants = PATH_PACKAGE.parents[1] / 'tests' / 'constants.py'
    test_constants = SourceFileLoader("constants", str(path_testing_constants)).load_module()
    return test_constants