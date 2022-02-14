# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     formats: py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.13.6
#   kernelspec:
#     display_name: Python [conda env:ipyautoui]
#     language: python
#     name: conda-env-ipyautoui-xpython
# ---

# %run __init__.py
#  ^ this means that the local imports still work when running as a notebook
# %load_ext lab_black

# +
from typing import Optional, Callable, Any
from pydantic import BaseModel, Field
from ipyrun.constants import PATH_RUNAPP_HELP
from IPython.display import Image

des_config = """
a config object from which the actions are built. this allows RunActions to be inherited and validators to be added
that configure the actions based on the data in the config object.
"""
des_app = """
the app instance. this allows actions to be associated to the app using the validators.
"""


class RunActions(BaseModel):
    """map containing callables that are called when buttons in the RunApp are
    activated. Default values contain dummy calls. setting the values to "None"
    hides the button in the App. The actions here are used to show / hide another
    UI element that the user can edit."""

    config: Any = Field(None, description=des_config)
    app: Any = Field(None, description=des_app)
    save_config: Optional[Callable] = lambda: "save_config"
    check: Optional[Callable[[], Any]] = lambda: "check"
    uncheck: Optional[Callable] = lambda: "uncheck"
    get_status: Optional[Callable] = lambda: "get_status"
    update_status: Optional[Callable] = lambda: "update_status"
    help_ui_show: Optional[Callable] = lambda: 'help_ui_show' #Image(PATH_RUNAPP_HELP)
    help_ui_hide: Optional[Callable] = lambda: "help_ui_hide"
    help_run_show: Optional[Callable] = lambda: "help_run_show"
    help_run_hide: Optional[Callable] = lambda: "help_run_hide"
    help_config_show: Optional[Callable] = lambda: "help_config_show"
    help_config_hide: Optional[Callable] = lambda: "help_config_hide"
    inputs_show: Optional[Callable] = lambda: "inputs_show"
    inputs_hide: Optional[Callable] = lambda: "inputs_hide"
    outputs_show: Optional[Callable] = lambda: "outputs_show"
    outputs_hide: Optional[Callable] = lambda: "outputs_hide"
    runlog_show: Optional[Callable] = lambda: "runlog_show"
    runlog_hide: Optional[Callable] = lambda: "runlog_hide"
    run: Optional[Callable] = lambda: "run"
    run_hide: Optional[Callable] = lambda: "console_hide"
    activate: Optional[Callable] = lambda: "activate"
    deactivate: Optional[Callable] = lambda: "deactivate"
    show: Optional[Callable] = (lambda : 'show')
    hide: Optional[Callable] = (lambda : 'hide')


#  as the RunActions are so generic, the same actions can be applied to Batch operations
#  with the addition of some batch specific operations
class BatchActions(RunActions):
    """actions associated within managing a batch of RunApps. As with the RunActions,
    these actions just call in another UI element that does the actual work. See
    ui_add.py, ui_remove.py, ui_wizard.py

    Args:
        RunActions ([type]): [description]
    """

    add: Optional[Callable] = lambda: "add"  # ????/
    remove: Optional[Callable] = lambda: "remove"  # ????
    load: Optional[Callable] = lambda: "load"  # ????
    add_show: Optional[Callable] = lambda: "add_show"
    add_hide: Optional[Callable] = lambda: "add_hide"
    remove_show: Optional[Callable] = lambda: "remove_show"
    remove_hide: Optional[Callable] = lambda: "remove_hide"
    wizard_show: Optional[Callable] = lambda: "wizard_show"
    wizard_hide: Optional[Callable] = lambda: "wizard_hide"
    review_show: Optional[Callable] = lambda: "review_show"
    review_hide: Optional[Callable] = lambda: "review_hide"
    load_project: Optional[Callable] = lambda: "load_project"
