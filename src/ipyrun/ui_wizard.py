# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.13.3
#   kernelspec:
#     display_name: Python [conda env:ipyautoui]
#     language: python
#     name: conda-env-ipyautoui-xpython
# ---

# %%
"""
contains UI widget for adding and removing schedules
"""
# %run _dev_sys_path_append.py
# %run __init__.py
# %load_ext lab_black

# %%
import shutil
from typing import Callable
import uuid
import os
import pandas as pd
import ipywidgets as widgets
from IPython.display import display, Markdown, clear_output
from dataclasses import asdict, field
from dataclasses import dataclass
import functools

#  local imports
from ipyrun.constants import (
    FPTH_USER_ICON,
    FPTH_MXF_ICON,
    FPTH_TEMPLATE_PROCESSES,
    BUTTON_WIDTH_MIN,
    BUTTON_HEIGHT_MIN,
)
from ipyrun._utils import template_plus_button, make_dir

NBFDIR = os.path.dirname(os.path.realpath("__file__"))

IMG_USER = open(FPTH_USER_ICON, "rb").read()
IMG_MXF = open(FPTH_MXF_ICON, "rb").read()

FROM_TEMPLATE_IMG = {True: IMG_MXF, False: IMG_USER}


# %%
def return_alphanumeric_str(string):
    return "".join(e for e in string if e.isalnum())


# object definitions for 1no row of the select / add / remove interface
@dataclass
class SelectProcess:
    """state definition of a given schedule"""

    name: str = ""
    long_name: str = ""
    exists: bool = False
    fromTemplate: bool = False
    guid: uuid.uuid4 = field(
        default_factory=lambda: str(uuid.uuid4())
    )  # lambda means a new UUID is created each time its initialised

    def __post_init__(self):
        if self.long_name == "":
            self.long_name = self.name
        self.name = return_alphanumeric_str(self.long_name)


@dataclass
class SelectWidgetRow:
    """definition of an "SelectProcess" interface object with no styling.
    (the styling depends on the data within a SelectProcess object)"""

    create: widgets.Button = None
    remove: widgets.Button = None

    long_name: widgets.Text = None
    fromTemplate: widgets.Image = None
    row: widgets.HBox = None
    guid: uuid.uuid4 = None

    def __post_init__(self):
        self.create = widgets.Button(
            disabled=False,
            layout=widgets.Layout(width=BUTTON_WIDTH_MIN, height=BUTTON_HEIGHT_MIN),
        )
        self.remove = widgets.Button(
            disabled=False,
            layout=widgets.Layout(width=BUTTON_WIDTH_MIN, height=BUTTON_HEIGHT_MIN),
        )
        self.long_name = widgets.Text(disabled=True)
        self.fromTemplate = widgets.Image(
            format="png",
            width=BUTTON_HEIGHT_MIN,
            height=BUTTON_HEIGHT_MIN,
            layout=widgets.Layout(object_fit="contain"),
        )
        self.row = widgets.HBox(
            [self.create, self.remove, self.fromTemplate, self.long_name]
        )  # exists,


# %%
def style_widget_row(row: SelectWidgetRow, s: SelectProcess, debug: bool = False):
    """styles the "SelectWidgetRow" widget in-place based on data from the "SelectProcess" object
    """

    def check_remove_only(row: SelectWidgetRow, create_tooltip=""):
        # create
        row.create.icon = "check"
        row.create.tooltip = "already exists in project"
        row.create.button_style = "success"
        row.create.disabled = True
        # remove
        row.remove.tooltip = "remove from project"
        row.remove.icon = "trash"
        row.remove.button_style = "danger"
        row.remove.style.button_color = None
        row.remove.disabled = False

    row.long_name.value = s.long_name
    row.guid = s.guid

    if s.exists and s.fromTemplate:
        if debug:
            print("check. remove only. --> add. blank.")
        check_remove_only(
            row,
            create_tooltip=(
                "{} already exists in project. MXF standard schedule.".format(
                    s.long_name
                )
            ),
        )
        row.fromTemplate.value = FROM_TEMPLATE_IMG[True]
        row.long_name.disabled = True
    elif s.exists and not s.fromTemplate:
        if debug:
            print("check. remove only. --> add. remove from list.")
        check_remove_only(
            row,
            create_tooltip=(
                "{} already exists in project. Project defined schedule.".format(
                    s.long_name
                )
            ),
        )
        row.fromTemplate.value = FROM_TEMPLATE_IMG[False]
        row.long_name.disabled = True
    elif not s.exists and s.fromTemplate:
        if debug:
            print("add. blank. --> check. remove only.")
        row.fromTemplate.value = FROM_TEMPLATE_IMG[True]
        row.long_name.disabled = True
        # create
        row.create.disabled = False
        row.create.icon = "plus"
        row.create.button_style = "warning"
        row.create.tooltip = "add {} to project. MXF standard schedule.".format(
            s.long_name
        )
        # remove
        row.remove.tooltip = "cannot remove template processes from list"
        row.remove.button_style = ""
        row.remove.icon = (  #  this icon doesn't exist. but removes the old one to leave it blank (desired).
            "full"
        )
        row.remove.disabled = True
        row.remove.style.button_color = "white"

        if debug:
            print(f"row.remove.icon = {row.remove.icon}")
    elif not s.exists and not s.fromTemplate:
        if debug:
            print("add. remove from list. --> check. remove only.")
            print("                       --> row removed")
        # create
        row.create.disabled = False
        row.create.icon = "plus"
        row.create.button_style = "warning"
        row.create.tooltip = "add {} to project. Project defined schedule.".format(
            s.long_name
        )
        # remove
        row.remove.tooltip = "remove from list"
        row.remove.icon = "minus"
        row.remove.button_style = ""
        row.fromTemplate.value = FROM_TEMPLATE_IMG[False]
        row.long_name.disabled = False


def get_SelectProcess_from_SelectWidgetRow(row: SelectWidgetRow) -> SelectProcess:
    """
    pass a ui element and return the associated data-object.
    CURRENTLY ONLY IN USE FOR DEBUGGING.

    Args:
        row (SelectWidgetRow): row ui

    Returns:
        s (SelectProcess): data object
    """
    s = SelectProcess(long_name=row.long_name.value)
    if (
        row.create.tooltip
        == "{} already exists in project. MXF standard schedule.".format(s.long_name)
    ):
        s.exists = True
        s.fromTemplate = True
    elif "{} already exists in project. Project defined schedule.".format(s.long_name):
        s.exists = True
        s.fromTemplate = False
    elif "add {} to project. MXF standard schedule.".format(s.long_name):
        s.exists = False
        s.fromTemplate = True
    elif "add {} to project. Project defined schedule.".format(s.long_name):
        s.exists = False
        s.fromTemplate = True
    else:
        print("tooltip error")
    return s


def debug_style_widget_row():
    """debugs the "style_widget_row" fn by supplying it with the different data-permutations and displays the resulting styling options
    CURRENTLY ONLY IN USE FOR DEBUGGING."""
    row = SelectWidgetRow()
    row0 = SelectWidgetRow()
    row1 = SelectWidgetRow()
    row2 = SelectWidgetRow()
    row3 = SelectWidgetRow()
    print("-----------------")
    print("unstyled")
    display(row.row)
    print(get_SelectProcess_from_SelectWidgetRow(row))
    print("-----------------")
    style_widget_row(
        row0,
        SelectProcess(exists=True, fromTemplate=True, long_name="from template"),
        debug=True,
    )
    display(row0.row)
    print(get_SelectProcess_from_SelectWidgetRow(row0))
    print("-----------------")
    style_widget_row(
        row1,
        SelectProcess(exists=True, fromTemplate=False, long_name="user defined"),
        debug=True,
    )
    display(row1.row)
    print(get_SelectProcess_from_SelectWidgetRow(row1))
    print("-----------------")
    style_widget_row(
        row2,
        SelectProcess(exists=False, fromTemplate=True, long_name="from template"),
        debug=True,
    )
    display(row2.row)
    print(get_SelectProcess_from_SelectWidgetRow(row2))
    print("-----------------")
    style_widget_row(
        row3,
        SelectProcess(exists=False, fromTemplate=False, long_name="user defined"),
        debug=True,
    )
    display(row3.row)
    print(get_SelectProcess_from_SelectWidgetRow(row3))
    print("-----------------")


if __name__ == "__main__":
    debug_style_widget_row()


# %%
class AddRemoveScheduleForm:
    def __init__(
        self,
        fpth_processes: str,
        FPTH_TEMPLATE_PROCESSES: str = FPTH_TEMPLATE_PROCESSES,
    ):
        """UI form only. no controls."""
        self.out = widgets.Output()
        self.fpth_processes = fpth_processes
        if not os.path.isfile(self.fpth_processes):
            if not os.path.isdir(
                os.path.dirname(self.fpth_processes)
            ):  # repeated code in create_schedule_ui. probs a better way... check _runconfig working properly
                make_dir(os.path.dirname(self.fpth_processes))
            shutil.copyfile(FPTH_TEMPLATE_PROCESSES, self.fpth_processes)
        self.__df_processes = pd.read_csv(self.fpth_processes).set_index("guid")
        self._init_form()
        self._update_row_style()

    @property
    def df_processes(self):
        return self.__df_processes

    @df_processes.setter
    def df_processes(self, value):
        self.__df_processes = value
        self.__df_processes.reset_index().to_csv(self.fpth_processes, index=None)

    @property
    def guids(self):
        return self.df_processes.index.tolist()

    def _init_form(self):
        self.select_processes_widgets = [
            SelectWidgetRow(guid=guid) for guid in self.guids
        ]  # init blank ui rows
        self.add_user_defined = template_plus_button(
            description="", tooltip="add schedule to list"
        )
        self.select_processes = widgets.VBox(self.select_processes_children)

    def _update_row_style(self, guid=None):
        if guid is None:
            [
                style_widget_row(
                    self._get_select_processes_widget(guid),
                    self._get_SelectProcess_obj(guid),
                )
                for guid in self.guids
            ]
        else:
            style_widget_row(
                self._get_select_processes_widget(guid),
                self._get_SelectProcess_obj(guid),
                debug=False,
            )

    @property
    def row_widgets(self):
        return [s.row for s in self.select_processes_widgets]

    @property
    def select_processes_children(self):
        return self.row_widgets + [self.add_user_defined]

    def _get_SelectProcess_obj(self, guid):
        return SelectProcess(**self.df_processes.loc[guid], guid=guid)

    def _get_select_processes_widget(self, guid):
        return [s for s in self.select_processes_widgets if s.guid == guid][0]

    def display(self):
        display(self.out)
        display(self.select_processes)

    def _ipython_display_(self):
        self.display()


if __name__ == "__main__":
    add_remove = AddRemoveScheduleForm("processes-schedule.csv")
    display(add_remove)


# %%
def add_process(main_app, name, long_name):
    print("add_process called")


def remove_process(main_app, name):
    print("remove_process called")


class AddRemoveProcess(AddRemoveScheduleForm):
    """extends "AddRemoveScheduleForm" to provide controls.
    add_process and remove_process to be defined in the main create_schedule_ui and provide the link between this
    interface and the main app.

    Args:
        fpth_processes: csv with tabular list of processes in project and template processes to choose from
        FPTH_TEMPLATE_PROCESSES: template "fpth_processes"
        main_app: RunAppsprocesses class instance
        add_process: a function that is passed to this class to operate on the main_app to add extra processes
            to the project. executed as follows:
            self.add_process(self.main_app)
        remove_process: as above for removing processes from the project.
    """

    def __init__(
        self,
        fpth_processes: str,
        FPTH_TEMPLATE_PROCESSES: str = FPTH_TEMPLATE_PROCESSES,
        main_app=None,  #: RunApps
        add_process: Callable = add_process,
        remove_process: Callable = remove_process,
    ):
        super().__init__(fpth_processes)
        self.main_app = main_app
        self.add_process = add_process  # function operates on main_app to add schedule
        self.remove_process = (
            remove_process  # function operates on main_app to remove schedule
        )
        self._init_controls()

    def _init_controls(self):
        [self._init_row_controls(guid) for guid in self.guids]
        self.add_user_defined.on_click(self._add_user_defined)

    def _init_row_controls(self, guid):
        self._get_select_processes_widget(guid).create.on_click(
            functools.partial(self._create, guid=guid)
        )
        self._get_select_processes_widget(guid).long_name.observe(
            self._update_change_name, "value"
        )
        self._get_select_processes_widget(guid).remove.on_click(
            functools.partial(self._remove, guid=guid)
        )

    def _create(self, onclick, guid=None):
        name = self.df_processes.loc[guid, "name"]
        long_name = self.df_processes.loc[guid, "long_name"]
        if self._is_unique(name):
            self._display_message(f"added to project: {name}")
            self.add_process(self.main_app, name, long_name)
            tmp = self.df_processes
            tmp.loc[guid, "exists"] = True
            self.df_processes = tmp
            self._update_row_style(guid=guid)
        else:
            self._display_message(f"ERROR - already exists in project: {name}")

    def _remove_from_list(self, guid, name):
        self._display_message(f"removed from list: {name}")
        tmp = self.df_processes
        tmp = tmp.drop([guid])
        self.df_processes = tmp
        self.select_processes_widgets.remove(self._get_select_processes_widget(guid))
        self.select_processes.children = self.select_processes_children

    def _remove_from_project(self, guid, name):
        self._display_message(f"removed from project: {name}")
        tmp = self.df_processes
        tmp.loc[guid, "exists"] = False
        self.df_processes = tmp
        self._update_row_style(guid=guid)
        self.remove_process(self.main_app, name)

    def _remove(self, onclick, guid=None):
        name = self.df_processes.loc[guid, "name"]
        if (
            not self.df_processes.loc[guid, "exists"]
            and not self.df_processes.loc[guid, "fromTemplate"]
        ):
            # if not in project, and user defined
            self._remove_from_list(guid, name)
        elif self.df_processes.loc[guid, "exists"]:
            # if in project, just return to list
            self._remove_from_project(guid, name)
        else:
            self._display_message("ERROR WHEN REMOVING: {}".format(name))

    def _add_user_defined(self, onclick):
        add = SelectProcess()
        tmp = self.df_processes
        tmp = tmp.append(
            pd.DataFrame.from_dict(asdict(add), orient="index").T.set_index("guid")
        )
        self.df_processes = tmp
        row = SelectWidgetRow(guid=add.guid)
        self.select_processes_widgets.append(row)
        self._update_row_style(guid=add.guid)
        self.select_processes.children = self.select_processes_children
        self._init_row_controls(add.guid)

    @property
    def schedule_names(self):
        return [s.long_name.value for s in self.select_processes_widgets]

    def _update_change_name(self, change):
        tmp = self.df_processes
        tmp["long_name"] = self.schedule_names
        tmp["name"] = [
            return_alphanumeric_str(string) for string in self.schedule_names
        ]
        self.df_processes = tmp

    def _is_unique(self, name):
        if (
            len(self.df_processes.query('exists == True and name == "{}"'.format(name)))
            == 0
        ):
            return True
        else:
            return False

    def _display_message(self, message):
        with self.out:
            clear_output()
            display(Markdown(message))

    def _df_processes_get_index(self, guid):
        return self.df_processes.query('guid == "{}"'.format(guid)).index[0]

    def _select_processes_widgets_get_index(self, guid):
        return [
            n
            for n in range(0, len(self.select_processes_widgets))
            if self.select_processes_widgets[n].guid == guid
        ][0]


if __name__ == "__main__":
    add_remove = AddRemoveProcess("processes-schedule.csv")
    display(add_remove)

# %%
