# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.4.2
#   kernelspec:
#     display_name: mf_base
#     language: python
#     name: mf_base
# ---

# +
import os
FDIR = os.path.dirname(os.path.realpath('__file__'))

from IPython.display import clear_output, display, Image, FileLink, FileLinks, JSON, Markdown, HTML
import ipywidgets as widgets
from shutil import copyfile
from markdown import markdown
from datetime import datetime
import time
from dataclasses import dataclass, field, asdict

from mf_modules.pydtype_operations import read_json, read_yaml
from ipyfilechooser import FileChooser

# from this repo
# this is an unpleasant hack. should aim to find a better solution
try:
    from ipyrun._runconfig import RunConfig, SimpleInputs, AppConfig
except:
    from _runconfig import RunConfig, SimpleInputs, AppConfig


# +
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


class Errors():

    def _errors(self):
        self.errors=[]
        self.iserror = False
        self.errormessage = 'no error'


class FileController(Errors):

    def __init__(self, inputs: SimpleInputs):
        self.out = widgets.Output()
        self.inputs = inputs
        self._inherit_Inputs()
        self._init_FileController()

    def _init_FileController(self):
        self._errors()
        self.file_control_form()
        self._init_control()

    def _inherit_Inputs(self):
        self.__dict__.update(**asdict(self.inputs))

    def _init_control(self):
        self.save_changes.on_click(self._save_changes)
        self.load_inputs.observe(self._load_inputs,'value')
        self.load_button.on_click(self._load)
        self.revert.on_click(self._revert)

    @property
    def mf_layout(self):
        return widgets.Layout(
            display='flex',
            flex_flow='row',
            justify_content='flex-start',
            #border='dashed 0.2px green',
            grid_auto_columns='False',
            width='100%',
            #align_items='stretch',
        )

    def file_control_form(self):

        # button bar
        self.load_inputs = widgets.ToggleButton(icon='folder-open',tooltip='open inputs from file',button_style='info',layout=widgets.Layout(width='50px'))# (FontAwesome names without the `fa-` prefix)
        self.revert = widgets.Button(icon='fa-undo',tooltip='revert to last save',button_style='warning',style={'font_weight':'bold'},layout=widgets.Layout(width='50px'))#,button_style='success'
        self.save_changes = widgets.Button(icon='fa-save',tooltip='save changes',button_style='success',layout=widgets.Layout(width='50px'))
        self.button_bar = widgets.HBox([ self.load_inputs, self.revert, self.save_changes])

        # nested buttons
        template_inputs = self.get_template_inputs()
        project_inputs = self.get_project_inputs()
        options = dict(template_inputs, **project_inputs)
        self.load_button = widgets.Button(description = 'load',icon='fa-upload',style={'font_weight':'bold'})
        self.choose_inputs = widgets.RadioButtons(
            options = options,
            layout = self.mf_layout,
        )
        self.load = widgets.VBox([self.load_button,self.choose_inputs])
        self.temp_message = widgets.HTML(markdown('edit user input form below'))
        self.inputform = widgets.VBox([], layout = self.mf_layout)

    def _revert(self, sender):
        """revert to last save of working inputs file"""
        fpth = self.fpth_inputs
        self.temp_message.value = markdown('revert to inputs in last save of: {0}'.format(fpth))

        # add code here to revert to last save

        self.update_display()
        self.display()

    def _save_changes(self, sender):
        """save changes to working inputs file"""
        fpth = self.fpth_inputs
        dateTimeObj = datetime.now()
        self.save_timestampStr = dateTimeObj.strftime("%d-%b-%Y %H:%M:%S")
        self.temp_message.value = markdown('{0} saved at: {1}'.format(fpth, self.save_timestampStr))

        # add code here to save changes to file

        self.update_display()
        self.display()

    def _load_inputs(self,sender):
        """launches the inputs from file dialog"""
        self.temp_message.value = markdown('update the user input form with data from file')
        if self.load_inputs.value:
            self.inputform.children = [self.load_button, self.choose_inputs]
        else:
            self.temp_message.value = markdown('')
            self.inputform.children = []
        self.update_display()
        self.display()

    def _load(self,sender):
        self.update_display()
        self.display()
        fpth = self.choose_inputs.value

        # add code here to load form from file

        self.temp_message.value = markdown('input form load data from: {0}'.format(fpth))
        try:
            self.iserror = False
            message = 'load input form from: {0}'.format(fpth)
        except:
            self.iserror = True
            self.errormessage = '''__error__ loading : {0}.
            the file has either been deleted or modified such that it is unreadable'''.format(fpth)
        with self.out:
            clear_output()
            if self.load_inputs.value:
                display(Markdown(message))
            if self.iserror:
                display(Markdown(self.errormessage))

    def get_project_inputs(self):
        fpths = self.fpth_inputs_options['project']['fpths']
        di = {}
        for fpth in fpths:
            description = 'PROJECT: '+ fpth
            di[description] = fpth
        return di

    def get_template_inputs(self):
        fpths = self.fpth_inputs_options['template']['fpths']
        di = {}
        for fpth in fpths:
            description = 'TEMPLATE: '+ fpth
            di[description] = fpth
        return di

    def update_display(self):
        box = widgets.VBox([
            self.button_bar,
            self.temp_message,
            self.inputform,
        ])
        self.layout = box

    def display(self):
        display(self.layout)
        display(self.out)

    def _ipython_display_(self):
        self.update_display()
        self.display()


class FileConfigController(RunConfig, FileController, Errors):

    """
    class that combines RunConfig and FileController - generating the filepaths
    of the inputs and working files
    """

    def __init__(self,config: AppConfig):
        self._init_FileConfigController(config)

    def _init_FileConfigController(self, config):
        self.out = widgets.Output()
        self._errors()
        self._init_RunConfig(config)
        self._init_FileController()


    def _revert(self, sender):
        """revert to last save of working inputs file"""
        fpth = self.fpth_inputs
        self.temp_message.value = markdown('revert to inputs in last save of: {0}'.format(fpth))

        # add code here to revert to last save

        self.update_display()
        self.display()

    def _save_changes(self, sender):
        """save changes to working inputs file"""
        fpth = self.fpth_inputs
        dateTimeObj = datetime.now()
        self.save_timestampStr = dateTimeObj.strftime("%d-%b-%Y %H:%M:%S")
        self.temp_message.value = markdown('{0} saved at: {1}'.format(fpth, self.save_timestampStr))

        # add code here to save changes to file

        self.update_display()
        self.display()

    def _load_inputs(self,sender):
        """launches the inputs from file dialog"""
        self.temp_message.value = markdown('update the user input form with data from file')
        if self.load_inputs.value:
            self.inputform.children = [self.load_button, self.choose_inputs]
        else:
            self.temp_message.value = markdown('')
            self.inputform.children = []
        self.update_display()
        self.display()

    def _load(self,sender):
        self.update_display()
        self.display()
        fpth = self.choose_inputs.value

        # add code here to load form from file

        self.temp_message.value = markdown('input form load data from: {0}'.format(fpth))
        try:
            self.iserror = False
            message = 'load input form from: {0}'.format(fpth)
        except:
            self.iserror = True
            self.errormessage = '''__error__ loading : {0}.
            the file has either been deleted or modified such that it is unreadable'''.format(fpth)
        with self.out:
            clear_output()
            if self.load_inputs.value:
                display(Markdown(message))
            if self.iserror:
                display(Markdown(self.errormessage))

class SelectEditSaveMfJson():
    def __init__(self, fdir, fnm=None):
        self._init_SelectEditSaveMfJson(fdir, fnm=fnm)

    def _init_SelectEditSaveMfJson(self, fdir, fnm=None):
        self.out = widgets.Output()
        self.fdir = fdir
        self.fnm = fnm
        self.file_control_form()
        self._init_control()

    @property
    def mf_layout(self):
        return widgets.Layout(
            display='flex',
            flex_flow='row',
            justify_content='flex-start',
            #border='dashed 0.2px green',
            grid_auto_columns='False',
            width='100%',
            #align_items='stretch',
        )

    def file_control_form(self):

        # button bar
        self.select_file = widgets.ToggleButton(description='select file',button_style='info',style={'font_weight':'bold'})
        self.edit_file = widgets.ToggleButton(description='edit file',button_style='warning',style={'font_weight':'bold'})
        self.save_changes = widgets.Button(description='save changes',button_style='success',style={'font_weight':'bold'})
        self.button_bar = widgets.HBox([self.select_file,self.edit_file, self.save_changes])

        # nested
        self.file_chooser = FileChooser(self.fdir)
        if self.fnm != None:
            self.file_chooser.reset(path=self.fdir, filename=self.fnm)
        self.temp_message = widgets.HTML(markdown('edit user input form below'))
        self.inputform = widgets.VBox([], layout = self.mf_layout)

    def _init_control(self):
        self.save_changes.on_click(self._save_changes)
        self.select_file.observe(self._select_file,'value')
        self.edit_file.observe(self._edit_file,'value')

    def _save_changes(self, sender):
        """save changes to working inputs file"""
        fpth = self.file_chooser.selected
        dateTimeObj = datetime.now()
        self.save_timestampStr = dateTimeObj.strftime("%d-%b-%Y %H:%M:%S")
        self.temp_message.value = markdown('{0} saved at: {1}'.format(fpth, self.save_timestampStr))

        # add code here to save changes to file

        self.update_sse_display()
        self.sse_display()

    def _edit_file(self, sender):
        """save changes to working inputs file"""
        fpth = self.file_chooser.selected
        self.temp_message.value = markdown('edit inputs below and save to: {0}'.format(fpth))

        # add code here to save changes to file

        self.update_sse_display()
        self.sse_display()

    def _select_file(self,sender):
        """launches the inputs from file dialog"""
        if self.select_file.value:
            self.temp_message.value = markdown('update the user input form with data from file')
            self.inputform.children = [self.file_chooser]
        else:
            self.temp_message.value = markdown('')
            self.inputform.children = []
        self.update_sse_display()
        self.sse_display()


    def update_sse_display(self):
        self.layout = widgets.VBox([
            self.button_bar,
            self.temp_message,
            self.inputform
        ])


    def sse_display(self):
        display(self.layout)

    def _ipython_display_(self):
        self.update_sse_display()
        self.sse_display()



# -

if __name__ == "__main__":

    # Example0: testing the FileController class only
    fpth_inputs_options = {
        'template': {
            'fdir': 'C:\\engDev\\git_mf\\MF_Toolbox\\dev\\mf_scripts\\template_inputs',
            'fpths': ['C:\\engDev\\git_mf\\MF_Toolbox\\dev\\mf_scripts\\template_inputs\\inputs-eplus_pipework_params.csv']
        },
        'project': {
            'fdir': '.\\appdata\\inputs\\archive',
            'fpths': [
                '.\\appdata\\inputs\\inputs-eplus_pipework_params-1.csv',
                '.\\appdata\\inputs\\inputs-eplus_pipework_params.csv',
                '.\\appdata\\inputs\\archive\\20200605-1625-inputs-eplus_pipework_params.csv',
                '.\\appdata\\inputs\\archive\\20200605-1625inputs-eplus_pipework_params.csv',
                '.\\appdata\\inputs\\archive\\20200607_1420-jg-inputs-eplus_pipework_params.csv'
            ]
        },
        'working': {
            'fdir': '.\\appdata\\inputs',
            'fpths': ['.\\appdata\\inputs\\inputs-eplus_pipework_params.csv']
        },
    }
    inputs = {
        'fdir_inputs': '.\\appdata\\inputs\\archive',
        'fdir_template_inputs': 'C:\\engDev\\git_mf\\MF_Toolbox\\dev\\mf_scripts\\template_inputs',
        'fpth_inputs': '.\\appdata\\inputs\\inputs-eplus_pipework_params.csv',
        'fpth_inputs_options':
            {
                'project': {
                    'fdir': '.\\appdata\\inputs\\archive',
                    'fpths': [
                '.\\appdata\\inputs\\inputs-eplus_pipework_params-1.csv',
                '.\\appdata\\inputs\\inputs-eplus_pipework_params.csv',
                '.\\appdata\\inputs\\archive\\20200605-1625-inputs-eplus_pipework_params.csv',
                '.\\appdata\\inputs\\archive\\20200605-1625inputs-eplus_pipework_params.csv',
                '.\\appdata\\inputs\\archive\\20200607_1420-jg-inputs-eplus_pipework_params.csv'
            ]
                },
                'template': {
                    'fdir': 'fdir_template_inputs',
                    'fpths': ['C:\\engDev\\git_mf\\MF_Toolbox\\dev\\mf_scripts\\template_inputs\\inputs-eplus_pipework_params.csv']
                }
            }
        }
    inputs = SimpleInputs(**inputs)
    d = FileController(inputs)
    # display
    display(Markdown('### Example0 - Simple FileController'))
    display(Markdown('''Simple FileController. Used for testing only.'''))
    display(d)
    display(Markdown('---'))
    display(Markdown(''))

    # Example1
    config={
    'fpth_script':os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),
    'fdir':'.',
    }
    fc = FileConfigController(config)
    display(Markdown('### Example1 - FileConfigController'))
    display(Markdown('''
FileConfigController. \n
in the example above, fpth_inputs_options is passed as an input. but when using the RunApp it
is generated by the RunConfig script... so we can just inherit that and make a combined class with all of
the methods... (i.e. relies on passing a python file which has an associated template inputs file that is
found by the RunConfig class)'''))
    display(fc)
    display(Markdown('---'))
    display(Markdown(''))


    # Example2
    fdir = r'.'
    fnm = 'default_config.yaml'
    simpleedit = SelectEditSaveMfJson(fdir,fnm=fnm)
    # display
    display(Markdown('### Example2 - SelectEditSaveMfJson'))
    display(Markdown('''
SelectEditSaveMfJson. \n
in the it may be useful sometimes to consider the the JSON editor independently on the RunApp.
either for testing purposes or other future unknown applications. this class allows users to
navigate to a file and select it. It will then be merged with the JsonEdit class to allow
users to edit the JSON file'''))
    display(simpleedit)
    display(Markdown('---'))
    display(Markdown(''))
