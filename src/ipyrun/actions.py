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
import functools
from typing import Optional, Callable, Any
from pydantic import Field, validator
from markdown import markdown

from IPython.display import Image, clear_output, display
from ipywidgets import widgets

from ipyrun.constants import PATH_RUNAPP_HELP
from ipyrun.basemodel import BaseModel

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
    help_ui_show: Optional[Callable] = lambda: "help_ui_show"  # Image(PATH_RUNAPP_HELP)
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
    load_show: Optional[Callable] = lambda: display(widgets.HTML("load_show"))
    load_hide: Optional[Callable] = lambda: display(widgets.HTML("load_hide"))
    load: Optional[Callable] = lambda: display(widgets.HTML("load"))
    get_loaded: Optional[Callable] = lambda: display(widgets.HTML("get_loaded"))
    open_loaded: Optional[Callable] = lambda: display(widgets.HTML("open_loaded"))
    run: Optional[Callable] = lambda: "run"
    run_hide: Optional[Callable] = lambda: "console_hide"
    activate: Optional[Callable] = lambda: "activate"
    deactivate: Optional[Callable] = lambda: "deactivate"
    show: Optional[Callable] = lambda: "show"
    hide: Optional[Callable] = lambda: display(widgets.HTML("hide"))


def display_runui_tooltips(runui):
    """pass a ui object and display all items that contain tooltips with the tooltips exposed"""
    li = [k for k, v in runui.map_actions.items() if v is not None]
    li = [l for l in li if "tooltip" in l.__dict__["_trait_values"]]
    return widgets.VBox(
        [widgets.HBox([l, widgets.HTML(markdown(f"*{l.tooltip}*"))]) for l in li]
    )


def show(app):
    app.help_ui.value = False
    app.help_run.value = False
    app.help_config.value = False
    app.inputs.value = True
    app.outputs.value = True
    app.runlog.value = True


def hide(app):
    app.help_ui.value = False
    app.help_run.value = False
    app.help_config.value = False
    app.inputs.value = False
    app.outputs.value = False
    app.runlog.value = False
    with app.out_console:
        clear_output()


class DefaultRunActions(RunActions):
    @validator("show", always=True)
    def _show(cls, v, values):
        return None

    @validator("hide", always=True)
    def _hide(cls, v, values):
        return None

    @validator("activate", always=True)
    def _activate(cls, v, values):
        return functools.partial(show, values["app"])

    @validator("deactivate", always=True)
    def _deactivate(cls, v, values):
        return functools.partial(hide, values["app"])

    @validator("help_ui_show", always=True)
    def _help_ui_show(cls, v, values):
        return functools.partial(display_runui_tooltips, values["app"])


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
    add_show: Optional[Callable] = lambda: "add_show"
    add_hide: Optional[Callable] = lambda: "add_hide"
    remove_show: Optional[Callable] = lambda: "remove_show"
    remove_hide: Optional[Callable] = lambda: "remove_hide"
    wizard_show: Optional[Callable] = lambda: "wizard_show"
    wizard_hide: Optional[Callable] = lambda: "wizard_hide"
    review_show: Optional[Callable] = lambda: "review_show"
    review_hide: Optional[Callable] = lambda: "review_hide"


class DefaultBatchActions(DefaultRunActions):
    """actions associated within managing a batch of RunApps. As with the RunActions,
    these actions just call in another UI element that does the actual work. See
    ui_add.py, ui_remove.py, ui_wizard.py

    Args:
        RunActions ([type]): [description]
    """

    add: Optional[Callable] = lambda: "add"  # ????/
    remove: Optional[Callable] = lambda: "remove"  # ????
    add_show: Optional[Callable] = lambda: "add_show"
    add_hide: Optional[Callable] = lambda: "add_hide"
    remove_show: Optional[Callable] = lambda: "remove_show"
    remove_hide: Optional[Callable] = lambda: "remove_hide"
    wizard_show: Optional[Callable] = lambda: "wizard_show"
    wizard_hide: Optional[Callable] = lambda: "wizard_hide"
    review_show: Optional[Callable] = lambda: "review_show"
    review_hide: Optional[Callable] = lambda: "review_hide"

