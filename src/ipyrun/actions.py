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

# %run _dev_sys_path_append.py
# %run __init__.py
# %load_ext lab_black

# +
import functools
from typing import Optional, Callable, Any, Dict, Callable
from pydantic import Field, ValidationInfo, field_validator, ConfigDict

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


class RunActions(BaseModel, validate_assignment=True):
    """map containing callables that are called when buttons in the RunApp are
    activated. Default values contain dummy calls. setting the values to "None"
    hides the button in the App. The actions here are used to show / hide another
    UI element that the user can edit."""

    config: Any = Field(
        None, description=des_config, validate_default=True, check_fields=False
    )
    app: Any = Field(None, description=des_app)
    save_config: Optional[Callable] = Field(
        lambda: "save_config", validate_default=True
    )
    check: Optional[Callable[[], Any]] = Field(lambda: "check", validate_default=True)
    uncheck: Optional[Callable] = Field(lambda: "uncheck", validate_default=True)
    get_status: Optional[Callable] = Field(lambda: "get_status", validate_default=True)
    update_status: Optional[Callable] = Field(
        lambda: "update_status", validate_default=True
    )
    renderers: Optional[Dict[str, Callable]] = Field(
        None,
        description="renderer UI objects that get attached to AutoDisplay",
        exclude=True,
        validate_default=True,
    )
    help_ui_show: Optional[Callable] = Field(
        lambda: "help_ui_show", validate_default=True
    )
    help_ui_hide: Optional[Callable] = Field(
        lambda: "help_ui_hide", validate_default=True
    )
    help_run_show: Optional[Callable] = Field(
        lambda: "help_run_show", validate_default=True
    )
    help_run_hide: Optional[Callable] = Field(
        lambda: "help_run_hide", validate_default=True
    )
    help_config_show: Optional[Callable] = Field(
        lambda: "help_config_show", validate_default=True
    )
    help_config_hide: Optional[Callable] = Field(
        lambda: "help_config_hide", validate_default=True
    )
    inputs_show: Optional[Callable] = Field(
        lambda: "inputs_show", validate_default=True
    )
    inputs_hide: Optional[Callable] = Field(
        lambda: "inputs_hide", validate_default=True
    )
    outputs_show: Optional[Callable] = Field(
        lambda: "outputs_show", validate_default=True
    )
    outputs_hide: Optional[Callable] = Field(
        lambda: "outputs_hide", validate_default=True
    )
    runlog_show: Optional[Callable] = Field(
        lambda: "runlog_show", validate_default=True
    )
    runlog_hide: Optional[Callable] = Field(
        lambda: "runlog_hide", validate_default=True
    )
    upload_show: Optional[Callable] = Field(
        lambda: display(widgets.HTML("upload_show")), validate_default=True
    )
    upload_hide: Optional[Callable] = Field(
        lambda: display(widgets.HTML("upload_hide")), validate_default=True
    )
    load_show: Optional[Callable] = Field(
        lambda: display(widgets.HTML("load_show")), validate_default=True
    )
    load_hide: Optional[Callable] = Field(
        lambda: display(widgets.HTML("load_hide")), validate_default=True
    )
    load: Optional[Callable] = Field(
        lambda: display(widgets.HTML("load")), validate_default=True
    )
    get_loaded: Optional[Callable] = Field(
        lambda: display(widgets.HTML("get_loaded")), validate_default=True
    )
    run: Optional[Callable] = Field(lambda: "run", validate_default=True)
    run_hide: Optional[Callable] = Field(lambda: "console_hide", validate_default=True)
    activate: Optional[Callable] = Field(lambda: "activate", validate_default=True)
    deactivate: Optional[Callable] = Field(lambda: "deactivate", validate_default=True)
    show: Optional[Callable] = Field(lambda: "show", validate_default=True)
    hide: Optional[Callable] = Field(
        lambda: display(widgets.HTML("hide")), validate_default=True
    )


def display_runui_tooltips(runui):
    """pass a ui object and display all items that contain tooltips with the tooltips exposed"""
    li = [k for k, v in runui.map_actions.items() if v is not None]
    li = [l for l in li if "tooltip" in l.__dict__["_trait_values"]]
    return widgets.VBox(
        [widgets.HBox([l, widgets.HTML(f"<b>{l.tooltip}</b>")]) for l in li]
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
    @field_validator("show")
    def _show(cls, v: int, info: ValidationInfo):
        return None

    @field_validator("hide")
    def _hide(cls, v: int, info: ValidationInfo):
        return None

    @field_validator("activate")
    def _activate(cls, v: int, info: ValidationInfo):
        return functools.partial(show, info.data["app"])

    @field_validator("deactivate")
    def _deactivate(cls, v: int, info: ValidationInfo):
        return functools.partial(hide, info.data["app"])

    @field_validator("help_ui_show")
    def _help_ui_show(cls, v: int, info: ValidationInfo):
        return functools.partial(display_runui_tooltips, info.data["app"])


#  as the RunActions are generic, the same actions can be applied to Batch operations
#  with the addition of some batch specific operations
class BatchActions(RunActions):
    """actions associated within managing a batch of RunApps. As with the RunActions,
    these actions just call in another UI element that does the actual work. See
    ui_add.py, ui_remove.py, ui_wizard.py

    Args:
        RunActions ([type]): [description]
    """

    add: Optional[Callable] = Field(lambda: "add", validate_default=True)
    remove: Optional[Callable] = Field(lambda: "remove", validate_default=True)
    add_show: Optional[Callable] = Field(lambda: "add_show", validate_default=True)
    add_hide: Optional[Callable] = Field(lambda: "add_hide", validate_default=True)
    remove_show: Optional[Callable] = Field(
        lambda: "remove_show", validate_default=True
    )
    remove_hide: Optional[Callable] = Field(
        lambda: "remove_hide", validate_default=True
    )
    wizard_show: Optional[Callable] = Field(
        lambda: "wizard_show", validate_default=True
    )
    wizard_hide: Optional[Callable] = Field(
        lambda: "wizard_hide", validate_default=True
    )
    review_show: Optional[Callable] = Field(
        lambda: "review_show", validate_default=True
    )
    review_hide: Optional[Callable] = Field(
        lambda: "review_hide", validate_default=True
    )


class DefaultBatchActions(DefaultRunActions):
    """actions associated within managing a batch of RunApps. As with the RunActions,
    these actions just call in another UI element that does the actual work. See
    ui_add.py, ui_remove.py, ui_wizard.py

    Args:
        RunActions ([type]): [description]
    """

    add: Optional[Callable] = Field(lambda: "add", validate_default=True)
    remove: Optional[Callable] = Field(lambda: "remove", validate_default=True)
    add_show: Optional[Callable] = Field(lambda: "add_show", validate_default=True)
    add_hide: Optional[Callable] = Field(lambda: "add_hide", validate_default=True)
    remove_show: Optional[Callable] = Field(
        lambda: "remove_show", validate_default=True
    )
    remove_hide: Optional[Callable] = Field(
        lambda: "remove_hide", validate_default=True
    )
    wizard_show: Optional[Callable] = Field(
        lambda: "wizard_show", validate_default=True
    )
    wizard_hide: Optional[Callable] = Field(
        lambda: "wizard_hide", validate_default=True
    )
    review_show: Optional[Callable] = Field(
        lambda: "review_show", validate_default=True
    )
    review_hide: Optional[Callable] = Field(
        lambda: "review_hide", validate_default=True
    )

    model_config = ConfigDict(check_fields=False)
