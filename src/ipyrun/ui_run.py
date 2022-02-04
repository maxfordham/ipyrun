# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
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

"""
contains core UI elements and dummy definitions for RunActions and BatchActions.
This creates a generic interface upon which functions for running workflows can be mapped onto.
"""
# %run __init__.py
# %load_ext lab_black

# +
import functools
from markdown import markdown

# object models
from typing import Optional, List, Dict, Type, Callable, Any
from pydantic.dataclasses import dataclass
from pydantic import BaseModel, validator, Field

# widget stuff
import traitlets
from IPython.display import (
    # update_display,
    display,
    Image,
    # JSON,
    Markdown,
    # HTML,
    clear_output,
)
import ipywidgets as widgets
import plotly.io as pio
import plotly.graph_objects as go
from halo import HaloNotebook

# core mf_modules
from ipyautoui.constants import TOGGLEBUTTON_ONCLICK_BORDER_LAYOUT
from ipyautoui.custom import Dictionary, RunName, LoadProject #VArray, 

# from this repo
from ipyrun.schema_actions import RunActions, BatchActions
from ipyrun.utils import make_dir, del_matching
from ipyrun.constants import (
    load_test_constants,
    BUTTON_WIDTH_MIN,
    BUTTON_WIDTH_MEDIUM,
    JOBNO_DEFAULT,
    PATH_RUNAPP_HELP,
    PATH_RUNAPPS_HELP,
)
from ipyrun.ui_add import AddRun
from ipyrun.ui_remove import RemoveRun
from ipyrun.constants import STATUS_BUTTON_NEEDSRERUN, STATUS_BUTTON_NOOUTPUTS, STATUS_BUTTON_UPTODATE, DI_STATUS_MAP, DEFAULT_BUTTON_STYLES
import immutables
frozenmap = (
    immutables.Map
)  # https://www.python.org/dev/peps/pep-0603/, https://github.com/MagicStack/immutables

def _markdown(value='_Markdown_',
              **kwargs):
    """
    a simple template for markdown text input that templates required input
    fields. additional user defined fields can be added as kwargs
    """
    _kwargs = {}
    _kwargs['value'] = markdown(value)  # required field
    _kwargs.update(kwargs)  # user overides
    return widgets.HTML(**_kwargs)
# +
class UiComponents():
    def __init__(self, button_styles=DEFAULT_BUTTON_STYLES):
        self._init_UiButtons(button_styles)

    @property
    def button_styles(self):
        return self._button_styles
    
    @button_styles.setter
    def button_styles(self, value):
        for k, v in value.items():
            [setattr(getattr(self, k), k_, v_) for k_, v_ in v.items()]
        self._button_styles = value
        
    def _init_UiButtons(self, button_styles=DEFAULT_BUTTON_STYLES):
        self.check = widgets.Checkbox()
        self.status_indicator = widgets.Button()
        self.help_ui = widgets.ToggleButton()
        self.help_run = widgets.ToggleButton()
        self.help_config = widgets.ToggleButton()
        self.inputs = widgets.ToggleButton()
        self.outputs = widgets.ToggleButton()
        self.runlog = widgets.ToggleButton()
        self.run = widgets.Button()
        self.show = widgets.Button()
        self.hide = widgets.Button()

        self.out_help_ui = widgets.Output()
        self.out_help_run = widgets.Output()
        self.out_help_config = widgets.Output()
        self.out_inputs = widgets.Output()
        self.out_outputs = widgets.Output()
        self.out_runlog = widgets.Output()
        self.out_console = widgets.Output()
        
        self.button_styles = button_styles
        

if __name__ == "__main__":
    display(widgets.VBox([widgets.HBox([widgets.HTML(f'<b>{k}</b>', layout={'width':'120px'}), v]) for k, v in UiComponents().__dict__.items() if k != "_button_styles"]))


# +
class RunUiConfig(BaseModel):
    include_show_hide = True
    
class RunActionsUi(traitlets.HasTraits, UiComponents):
    """maps the RunActions onto buttons. doesn't put them in a container.
    this is always used by the RunUi. the objects created here can then be placed
    appropriated in the RunUi container

    Returns:
        display: of buttons for testing
    """
    # TODO: make value == RunActions
    minwidth = BUTTON_WIDTH_MIN
    medwidth = BUTTON_WIDTH_MEDIUM
    _status = traitlets.Unicode()
    
    @traitlets.default('_status')
    def _default_status(self):
        return "no_outputs"
    
    @traitlets.validate("_status")
    def _validate_status(self, proposal):
        if proposal.value not in ["up_to_date", "no_outputs", "outputs_need_updating", "error"]:
            raise ValueError(
                f'{proposal} given. allowed values of "status" are: "up_to_date", "no_outputs", "outputs_need_updating", "error" only'
            )
        return proposal
    
    def __init__(self, actions: RunActions = RunActions(), button_styles=DEFAULT_BUTTON_STYLES):
        self._init_UiButtons(button_styles)
        self._init_RunActionsUi(actions)
        
        
    def _init_RunActionsUi(self, actions):
        self.status = 'no_outputs'
        self.actions = actions
        self._init_controls()
    
    @property
    def status(self):
        return self._status.value
    
    @status.setter
    def status(self, value):
        self._status = value
        self._style_status('click')
        
    # def _init_show_hide_functions(self):
    #     show_hide_buttons = ['help_ui', 'help_run', 'help_config', 'inputs', 'outputs', 'runlog']
    #     for b in show_hide_buttons:
    #         f = lambda self, on_change: self._show_hide_output(
    #             getattr(self, 'out_'+b),
    #             getattr(self, b),
    #             getattr(self.actions, b+'_show'),
    #             getattr(self.actions, b+'_hide')
    #         )
    #         setattr(self, '_'+b, f)

    def _init_controls(self):
        # show hide toggle widgets
        # self._init_show_hide_functions()
        self.help_ui.observe(self._help_ui, names="value")
        self.help_run.observe(self._help_run, names="value")
        self.help_config.observe(self._help_config, names="value")
        self.inputs.observe(self._inputs, names="value")
        self.outputs.observe(self._outputs, names="value")
        self.runlog.observe(self._runlog, names="value")
        
        self.run.on_click(self._run)
        self.check.observe(self._check, names="value")
        self.show.on_click(self._show)
        self.hide.on_click(self._hide)
        self.observe(self._status, names="status")
        self.status_indicator.on_click(self._status_indicator)

    def _style_status(self, change):
        style = dict(DI_STATUS_MAP[self.status])
        [setattr(self.status_indicator, k, v) for k, v in style.items()];

    def _status_indicator(self, onclick):
        self.actions.get_status()

    def _show(self, on_click):
        """default show run data. TODO - move to actions"""
        self.help_ui.value = False
        self.help_run.value = False
        self.help_config.value = False
        self.inputs.value = True
        self.outputs.value = True
        self.runlog.value = True

    def _hide(self, on_click):
        """default hide run data. TODO - move to actions"""
        self.help_ui.value = False
        self.help_run.value = False
        self.help_config.value = False
        self.inputs.value = False
        self.outputs.value = False
        self.runlog.value = False
        with self.out_console:
            clear_output()

    def _check(self, on_change):
        if self.check.value:
            self.actions.check()
        else:
            self.actions.uncheck()

    def _show_hide_output(
        self, widgets_output, widget_button, show_action, hide_action
    ):
        with widgets_output:
            if widget_button.value:
                widget_button.layout.border = TOGGLEBUTTON_ONCLICK_BORDER_LAYOUT  # 'solid yellow 2px'
                show = show_action()
                if show is not None:
                    display(show)
            else:
                widget_button.layout.border = ''
                hide_action()
                clear_output()

    def _help_ui(self, on_change):
        self._show_hide_output(
            self.out_help_ui,
            self.help_ui,
            self.actions.help_ui_show,
            self.actions.help_ui_hide,
        )

    def _help_run(self, on_change):
        self._show_hide_output(
            self.out_help_run,
            self.help_run,
            self.actions.help_run_show,
            self.actions.help_run_hide,
        )

    def _help_config(self, on_change):
        self._show_hide_output(
            self.out_help_config,
            self.help_config,
            self.actions.help_config_show,
            self.actions.help_config_hide,
        )

    def _inputs(self, on_change):
        self._show_hide_output(
            self.out_inputs,
            self.inputs,
            self.actions.inputs_show,
            self.actions.inputs_hide,
        )

    def _outputs(self, on_change):
        self._show_hide_output(
            self.out_outputs,
            self.outputs,
            self.actions.outputs_show,
            self.actions.outputs_hide,
        )

    def _runlog(self, on_change):
        self._show_hide_output(
            self.out_runlog, self.runlog, self.actions.runlog_show, self.actions.runlog_hide
        )

    def _run(self, on_change):
        with self.out_console:
            clear_output()
            self.run_hide = widgets.Button(
                layout={"width": BUTTON_WIDTH_MIN}, icon="fa-times", button_style="danger"
            )
            self.run_hide.on_click(self._run_hide)
            display(self.run_hide)
            self.actions.run()
            # reload outputs
            self.outputs.value = False
            self.outputs.value = True
            
    def _run_hide(self, click):
        with self.out_console:
            clear_output()

    def display(self):
        """note. this is for dev only. this class is designed to be inherited into a form
        where the display method is overwritten"""
        self.out = widgets.VBox(
            [
                widgets.HBox([self.help_ui, self.out_help_ui]),
                widgets.HBox([self.help_run, self.out_help_run]),
                widgets.HBox([self.help_config, self.out_help_config]),
                widgets.HBox([self.inputs, self.out_inputs]),
                widgets.HBox([self.outputs, self.out_outputs]),
                widgets.HBox([self.runlog, self.out_runlog]),
                widgets.HBox([self.check]),
                widgets.HBox([self.status_indicator]),
                widgets.HBox([self.run, self.out_console]),
                widgets.HBox([self.show]),
                widgets.HBox([self.hide]),
            ]
        )
        display(widgets.HTML("<b>Buttons to be programmed from `RunActions`</b> "))
        display(self.out)

    def _ipython_display_(self):
        self.display()

if __name__ == "__main__":

    display(
        Markdown(
            """
### RunActionsUi

These are all of the buttons that will be linked to callables in RunActions
    """
        )
    )
    display(Markdown("`>>> display(RunActionsUi())`"))
    run_actions_ui = RunActionsUi()
    display(run_actions_ui)
    # ui_actions1 = RunActionsUi()
    # display(ui_actions1)
# -

if __name__== "__main__":
    actions = RunActions()
    actions.inputs_show = lambda: 'asdfasfdasdfasdf'
    run_actions_ui.actions = actions
    run_actions_ui.status = 'up_to_date'


# +
class RunUi(widgets.HBox): #
    """takes run_actions object as an argument and initiates UI objects using 
    RunActionsUi. This class places these objects in containers to create a 
    more readable interface"""
    def __init__(self, run_actions=RunActions(), name='name', include_show_hide=True):
        super().__init__(layout=widgets.Layout(width='100%'))
        self.name = name
        self._init_show_hide(include_show_hide)
        self.ui = RunActionsUi(actions=run_actions) 
        self._layout_out()
        self._run_form()
    
    @property
    def actions(self):
        return self.ui.actions
    
    @actions.setter
    def actions(self, value):
        self.ui.actions = value
        self.update_form()

    def _init_show_hide(self, include_show_hide):
        if not include_show_hide:
            self.include_show_hide = None
        else:
            self.include_show_hide = include_show_hide
        
    def _layout_out(self): # TODO: update this so boxes empty
        self.layout_out = widgets.VBox(
            [
                widgets.HBox([self.ui.out_console]),
                widgets.HBox(
                    [self.ui.out_help_ui],
                    layout=widgets.Layout(
                        width="100%",
                        align_items="stretch",
                        justify_content="space-between",
                        align_content="stretch",
                    ),
                ),
                widgets.HBox(
                    [self.ui.out_help_run, self.ui.out_help_config],
                    layout=widgets.Layout(
                        width="100%",
                        align_items="stretch",
                        justify_content="space-between",
                        align_content="stretch",
                    ),
                ),
                widgets.HBox(
                    [self.ui.out_inputs, self.ui.out_outputs, self.ui.out_runlog],
                    layout=widgets.Layout(
                        width="100%",
                        align_items="stretch",
                        justify_content="space-between",
                        align_content="stretch",
                    ),
                ),
            ],
            layout=widgets.Layout(
                width="100%",
                align_items="stretch",
                align_content="stretch",
                display="flex",
                flex="flex-grow",
            ),
        )
        
    @property
    def button_map(self):
        return {
            "outside": {self.ui.check: self.ui.actions.check, self.ui.status_indicator: self.ui.actions.get_status},
            "left": {
                self.ui.help_ui: self.ui.actions.help_ui_show,
                self.ui.help_run: self.ui.actions.help_run_show,
                self.ui.help_config: self.ui.actions.help_config_show,
                self.show_hide_box: self.include_show_hide,
                self.ui.inputs: self.ui.actions.inputs_show,
                self.ui.outputs: self.ui.actions.outputs_show,
                self.ui.runlog: self.ui.actions.runlog_show,
                self.ui.run: self.ui.actions.run,
            },
            # "right": {self.ui.show: self.include_show_hide,
            #           self.ui.hide: self.include_show_hide},
        }
    
    def update_form(self):
        """update the form if the actions have changed"""
        self.button_bar_left.children = [k for k, v in self.button_map["left"].items() if v is not None]
        #self.button_bar_right.children = [k for k, v in self.button_map["right"].items() if v is not None]
        check = [k for k, v in self.button_map["outside"].items() if v is not None]
        self.children = check + [self.acc]
        self.acc.set_title(0, self.name)

    def _run_form(self):
        self.show_hide_box = widgets.HBox([self.ui.show, self.ui.hide],layout=widgets.Layout(align_items="stretch", border='solid LightSeaGreen')) #fcec90
        self.button_bar = widgets.HBox(layout=widgets.Layout(width="100%", justify_content="space-between"))
        self.button_bar_left = widgets.HBox(layout=widgets.Layout(align_items="stretch"))
        self.button_bar_right = widgets.HBox(layout=widgets.Layout(align_items="stretch"))
        self.button_bar.children = [self.button_bar_left, self.button_bar_right]
        self.acc = widgets.Accordion(
            children=[widgets.VBox([self.button_bar, self.layout_out])],
            selected_index=None,
            layout=widgets.Layout(width="100%"),
        )
        self.update_form()

if __name__ == "__main__":
    run_actions = RunActions()
    run_ui = RunUi(run_actions=run_actions)
    display(run_ui)

    run_actions1 = RunActions()
    run_ui1 = RunUi(run_actions=run_actions1)
    display(run_ui1)


# + tags=[]
class BatchActionsUi(RunActionsUi):
    """maps actions to buttons

    Args:
        RunActionsUi ([type]): inherits majority of definitions from RunActionsUi
    """

    def __init__(
        self, batch_actions: BatchActions = BatchActions()):
        self._init_BatchActionsUi(batch_actions)

    def _init_BatchActionsUi(self, actions):
        super().__init__(actions=actions)
        self._update_objects()
        self._update_controls()

    def _update_objects(self):
        self.add = widgets.ToggleButton(
            icon="plus",
            tooltip="add a run",
            style={"font_weight": "bold"},
            button_style="primary",
            layout=widgets.Layout(width=self.minwidth),
        )
        self.remove = widgets.ToggleButton(
            icon="minus",
            tooltip="add a run",
            style={"font_weight": "bold"},
            button_style="danger",
            layout=widgets.Layout(width=self.minwidth),
        )
        self.wizard = widgets.ToggleButton(
            icon="exchange-alt",
            tooltip="add a run",
            style={"font_weight": "bold"},
            button_style="warning",
            layout=widgets.Layout(width=self.minwidth),
        )
        self.load_project = LoadProject()
        self.out_add = widgets.Output()
        self.out_remove = widgets.Output()
        self.out_wizard = widgets.Output()

    def _update_controls(self):
        self.add.observe(self._add, names="value")
        self.remove.observe(self._remove, names="value")
        self.wizard.observe(self._wizard, names="value")

    def _add(self, on_change):
        self._show_hide_output(
            self.out_add, self.add, self.actions.add_show, self.actions.add_hide
        )

    def _remove(self, on_change):
        self._show_hide_output(
            self.out_remove,
            self.remove,
            self.actions.remove_show,
            self.actions.remove_hide,
        )

    def _wizard(self, on_change):
        self._show_hide_output(
            self.out_wizard,
            self.wizard,
            self.actions.wizard_show,
            self.actions.wizard_hide,
        )

    def display(self):
        """note. this is for dev only. this class is designed to be inherited into a form
        where the display method is overwritten"""
        out = widgets.VBox(
            [
                widgets.HBox([self.help_ui, self.out_help_ui]),
                widgets.HBox([self.help_run, self.out_help_run]),
                widgets.HBox([self.help_config, self.out_help_config]),
                widgets.HBox([self.inputs, self.out_inputs]),
                widgets.HBox([self.outputs, self.out_outputs]),
                widgets.HBox([self.runlog, self.out_runlog]),
                widgets.HBox([self.check]),
                widgets.HBox([self.run, self.out_console]),
                widgets.HBox([self.show]),
                widgets.HBox([self.hide]),
                self.load_project
            ]
        )
        display(
            widgets.HTML(
                """
Buttons to be programmed from `RunActions`. <br>
<b>NOTE. this class is a designed to be inherited by a container class. 
this display funtion is for testing only and will be overwritten</b>'
        """
            )
        )
        display(out)

        out_batch_only = widgets.VBox(
            [
                widgets.HBox([self.add, self.out_add]),
                widgets.HBox([self.remove, self.out_remove]),
                widgets.HBox([self.wizard, self.out_wizard]),
            ]
        )
        display(
            widgets.HTML(
                """
Buttons to be programmed from `BatchActions`. <br>
<b>NOTE. this class is a designed to be inherited by a container class. 
this display funtion is for testing only and will be overwritten</b>'
        """
            )
        )
        display(out_batch_only)

    def _ipython_display_(self):
        self.display()


if __name__ == "__main__":
    batch = BatchActionsUi()
    display(batch)
# -

from mf_file_utilities.constants import PATH_LINUXROOT
from ipyrun.constants import BUTTON_MIN_SIZE, BUTTON_WIDTH_MIN

# +
#import pathlib
#PROJECT_NUMBERS = [p.stem for p in pathlib.Path(PATH_LINUXROOT).glob('*')]


# +
def _fn_add(cls=None, name='name'):
    print(f'_fn_add: name={name}')
    ui_actions = RunActionsUi()
    cls.apps_box.add_row(new_key=name, add_kwargs={'name':name,'ui_actions':ui_actions})
    
def _fn_remove(cls=None, name='name'):
    print(f'_fn_remove: delete_data={delete_data}')
    
def _remove_show(cls=None):
    cls.apps_box.add_remove_controls = 'remove_only'
    fn = functools.partial(RemoveRun, app=cls, fn_remove=_fn_remove)
    return fn()

def _remove_hide(cls=None):
    cls.apps_box.add_remove_controls = None

class BatchUi(widgets.VBox):
    """Manage an array of RunApps

    Args:
        BatchActionsUi ([type]): [description]
    """

    def __init__(
        self,
        batch_actions: BatchActions(wizard_show = None),
        title: str = '# markdown batch title',
        include_show_hide=True,
        runs: Dict[str, Type[RunUi]]=None,
        fn_add=None,
        cls_runs_box=Dictionary,
    ):
        super().__init__(layout=widgets.Layout(width='100%'))
        self.cls_runs_box = cls_runs_box
        self.fn_add = fn_add
        self._init_show_hide(include_show_hide)
        self.ui = BatchActionsUi(batch_actions=batch_actions)  # ui_actions
        self.title = _markdown(title)
        self._layout_out()
        self._run_form()
        self._update_controls()
        if runs is None:
            runs = {}
        self.runs.items = runs

    @property
    def actions(self):
        return self.ui.actions
    
    @actions.setter
    def actions(self, value):
        self.ui.actions = value
        self.update_form()

    def _init_show_hide(self, include_show_hide):
        if not include_show_hide:
            self.include_show_hide = None
        else:
            self.include_show_hide = include_show_hide

    def _update_controls(self):
        self.ui.check.observe(self.check_all, names='value')

    def check_all(self, onchange):
        for k, v in self.apps.items():
            v.ui.check.value = self.ui.check.value

    @property
    def button_map(self):
        return {
            "outside": {self.ui.check: self.ui.actions.check},
            "left": {
                self.ui.help_ui: self.ui.actions.help_ui_show,
                self.ui.help_run: self.ui.actions.help_run_show,
                self.ui.help_config: self.ui.actions.help_config_show,
                self.show_hide_box: self.include_show_hide,
                self.ui.inputs: self.ui.actions.inputs_show,
                self.ui.outputs: self.ui.actions.outputs_show,
                self.ui.runlog: self.ui.actions.runlog_show,
                self.ui.run: self.ui.actions.run,
                self.ui.add: self.ui.actions.add_show,
                self.ui.remove: self.ui.actions.remove_show,
                self.ui.wizard: self.ui.actions.wizard_show,
            },
            # "right": {self.ui.show: self.include_show_hide,
            #           self.ui.hide: self.include_show_hide},
        }

    def _layout_out(self):
        self.layout_out = widgets.VBox(
            [
                widgets.HBox([self.ui.out_console]),
                widgets.HBox(
                    [self.ui.out_help_ui],
                    layout=widgets.Layout(
                        width="100%",
                        align_items="stretch",
                        justify_content="space-between",
                        align_content="stretch",
                    ),
                ),
                widgets.HBox(
                    [self.ui.out_add, self.ui.out_remove, self.ui.out_wizard],
                ),
                widgets.HBox(
                    [self.ui.out_help_run, self.ui.out_help_config],
                    layout=widgets.Layout(
                        width="100%",
                        align_items="stretch",
                        justify_content="space-between",
                        align_content="stretch",
                    ),
                ),
                widgets.HBox(
                    [self.ui.out_inputs, self.ui.out_outputs, self.ui.out_runlog],
                    layout=widgets.Layout(
                        width="100%",
                        align_items="stretch",
                        justify_content="space-between",
                        align_content="stretch",
                    ),
                ),
            ],
            layout=widgets.Layout(
                width="100%",
                align_items="stretch",
                align_content="stretch",
                display="flex",
                flex="flex-grow",
            ),
        )

    def update_form(self):
        """update the form if the actions have changed"""
        self.button_bar_left.children = [k for k, v in self.button_map["left"].items() if v is not None]
        #self.button_bar_right.children = [k for k, v in self.button_map["right"].items() if v is not None]
        check = [k for k, v in self.button_map["outside"].items() if v is not None]
        self.top_bar.children = check + [self.button_bar]
        self.children = [self.title, self.top_bar, self.layout_out, self.runs]

    def _run_form(self):
        self.show_hide_box = widgets.HBox([self.ui.show, self.ui.hide],layout=widgets.Layout(align_items="stretch", border='solid LightSeaGreen')) 
        self.button_bar = widgets.HBox(layout=widgets.Layout(width="100%", justify_content="space-between"))
        self.button_bar_left = widgets.HBox(layout=widgets.Layout(align_items="stretch"))
        self.button_bar_right = widgets.HBox(layout=widgets.Layout(align_items="stretch"))
        self.button_bar.children = [self.button_bar_left] + [self.button_bar_right] + [self.ui.load_project]
        self.top_bar = widgets.HBox(layout=widgets.Layout(width="100%", justify_content="space-between"))
        self.runs = self.cls_runs_box(toggle=False, watch_value=False, add_remove_controls=None, fn_add=self.fn_add, show_hash=None) 
        self.update_form()


if __name__ == "__main__":
    actions=RunActions()
    actions1=RunActions()
    run0 = RunUi(name='00-lean-description',run_actions=actions)
    run1 = RunUi(name='01-lean-description',run_actions=actions1)
    def add_show(cls=None):
        return 'add'
    batch_actions = BatchActions(add_show=add_show,
                                 inputs_show=None,
                                 outputs_show=None,
                                 runlog_show=None,
                                 wizard_show=None
                                # remove_show = functools.partial(_remove_show, cls=self),
                                # remove_hide = functools.partial(_remove_hide, cls=self)
                               )
    ui_actions = BatchActionsUi(batch_actions=batch_actions)
    run_batch = BatchUi(runs={'01-lean-description':run0, '02-lean-description':run1},batch_actions=batch_actions, fn_add=RunUi, include_show_hide=False)
    display(run_batch)


# +
# if __name__ == '__main__':
#     # from ipyrun._ipyeditcsv import EditRunAppCsv # TODO: i think there is an issue with "EditRunAppCsv" that needs fixing
#     # Example2 --------------------------
#     class RunAppEditCsvLineGraph(RunApp):

#         def __init__(self, config_app, app_config_revert_to_file=False):
#             super().__init__(config_app,app_config_revert_to_file=app_config_revert_to_file)

#         def _edit_inputs(self, sender):
#             with self.out:
#                 clear_output()
#                 display(EditRunAppCsv(self.config_app))

#         def execute(self):
#             fpth_csv = os.path.join(self.config_app.fdir, self.config_app.process_name + '-output.csv')
#             fpth_plotly = os.path.join(self.config_app.fdir, self.config_app.process_name + '-output.plotly.json')
#             subprocess.check_output(['python','-O', self.config_app.fpth_script, self.config_app.fpth_inputs, fpth_csv, fpth_plotly])
#             self.config_app.script_outputs = [Output(fpth_csv),Output(fpth_plotly)]


#     config_app_line_graph=AppConfig(
#             fpth_script=FPTH_SCRIPT_EXAMPLE_CSV,
#             fdir=FDIR_APP_EXAMPLE,
#             ftyp_inputs='csv'
#         )

#     rcsv = RunAppEditCsvLineGraph(config_app_line_graph)
#     display(rcsv)


# +
import pandas as pd
import getpass
import pathlib

def runlog(path_runlog): # TODO: do runlogging! 
    if type(path_runlog) == str:
        path_runlog = pathlib.Path(path_runlog)
    if path_runlog.is_file:
        self.df_runlog = del_matching(pd.read_csv(self.fpth_runlog),'Unnamed')
    else:
        di = {
            'processName':[],
            'user':[],
            'datetime':[],
            'formalIssue':[],
            'tags':[],
            'fpthInputs':[]
        }
        self.df_runlog = pd.DataFrame(di).rename_axis("index")

    user = getpass.getuser()
    timestamp = str(pd.to_datetime('today'))
    timestamp = timestamp[:-7]

    tmp = pd.DataFrame({
        'processName':[self.process_name],
        'user':[user],
        'datetime':[timestamp],
        'formalIssue':[''],
        'tags':[''],
        'fpthInputs':[self.fpth_inputs_archive]
    })
    self.df_runlog = self.df_runlog.append(tmp).reset_index(drop=True)
    make_dir(self.fdir_runlog)
    self.df_runlog.to_csv(self.fpth_runlog)
    return 
    
#path_runlog = '/mnt/c/engDev/git_mf/ipyrun/examples/J0000/test_appdir/appdata/runlog/runlog-expansion_vessel_sizing.csv'


# -
if __name__ == "__main__":
    display(Markdown('change add remove to ToggleButtons? (probs not)'))
    display(widgets.HBox([
        widgets.ToggleButtons(options = [('', 0), (' ', 1), ('  ', 2)], value=1,
                  icons=['plus','','minus'],
                  tooltips=['add a process','hide add / remove dialogue','remove a process'],
                  style=widgets.ToggleButtonsStyle(button_width='20px'),
                  layout=widgets.Layout(border='solid yellow')),
        ]))


