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
#     display_name: Python [conda env:mf_main] *
#     language: python
#     name: conda-env-mf_main-py
# ---

# +
import os 
FDIR = os.path.dirname(os.path.realpath('__file__'))
import pandas as pd
from IPython.display import Markdown, clear_output
import ipywidgets as widgets
from ipysheet import from_dataframe, to_dataframe
import ipysheet
from datetime import datetime
import time
from mf_modules.file_operations import make_dir

from pprint import pprint
from mf_modules.datamine_functions import time_meta_data
from mf_modules.pandas_operations import del_matching


# -

class EditCsv():

    def __init__(self, fpth_in, fpth_out=None):
        self.fpth_in = fpth_in
        if fpth_out==None:
            self.fpth_out = fpth_in
        else:
            self.fpth_out = fpth_out
        self.sheet = self._sheet_from_fpth(self.fpth_in)
        self.form()
        self._init_controls()
        self.out = widgets.Output()
        
    def form(self):
        self.save_changes = widgets.Button(description='save changes',button_style='success')
        self.button_bar = widgets.HBox([self.save_changes])
        self.layout = self.sheet
        
    def _init_controls(self):
        self.save_changes.on_click(self._save_changes)
        
    def _sheet_from_fpth(self, fpth):
        df=del_matching(pd.read_csv(fpth),'Unnamed')
        sheet = ipysheet.sheet(ipysheet.from_dataframe(df)) # initiate sheet
        return sheet
    
    def _save_changes(self, sender):
        self.data_out = to_dataframe(self.sheet)
        self.data_out.to_csv(self.fpth_out)
        display(Markdown('changes saved to: {0}'.format(self.fpth_out)))
        with self.out:
            clear_output()
            dateTimeObj = datetime.now()
            timestampStr = dateTimeObj.strftime("%d-%b-%Y %H:%M:%S:")
            display(Markdown('{0} changes saved to: {1}'.format(timestampStr,self.fpth_out)))
        self.display()

    def display(self):
        display(self.button_bar, self.out, self.layout)
        
    def _ipython_display_(self):
        self.display() 


if __name__ == "__main__":
    import os
    fpth = os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\configs\eplus_pipework_params.csv')
    editcsv = EditCsv(fpth)
    display(editcsv)

    
    config={
    'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),
    'fdir':'.',
    }
    from _runconfig import RunConfig
    from pprint import pprint
    rc = RunConfig(config)
    pprint(rc.config)
    pd.read_csv(rc.fpth_log)

# +

rc = RunConfig(config)


# +

from mf_modules.pandas_operations import del_matching


class EditRunCsv(EditCsv,RunConfig):
    
    def __init__(self, fpth_in, config, fpth_out=None):
        self.out = widgets.Output()
        self.config = config
        self.user_keys = list(config.keys())
        self.errors = []
        self._update_config()
        self.fpth_in = fpth_in
        if fpth_out==None:
            self.fpth_out = fpth_in
        else:
            self.fpth_out = fpth_out
        self.sheet = self._sheet_from_fpth(self.fpth_in)
        self.form()
        self._init_controls()
        self.iserror = False
        self.errormessage = 'no error'
        
        
    @property
    def mf_layout(self):
        return widgets.Layout(
            display='flex',
            flex_flow='row',
            justify_content='flex-start',
            #border='dashed 0.2px green',
            grid_auto_columns='True',
            width='100%',
            align_items='stretch',  
        )
        
    def form(self):
        
        # button bar
        self.save_changes = widgets.Button(description='save changes',button_style='success',style={'font_weight':'bold'})
        self.revert = widgets.Button(description='revert to last save',button_style='warning',style={'font_weight':'bold'})#,button_style='success'
        self.load_inputs = widgets.ToggleButton(description='inputs from file',button_style='info',style={'font_weight':'bold'})
        self.button_bar = widgets.HBox([self.save_changes,self.revert, self.load_inputs])
        
        # nested buttons
        template_inputs = self.get_template_inputs()
        project_inputs = self.get_logged_inputs()
        options = dict(template_inputs, **project_inputs)
        self.load_button = widgets.Button(description = 'load',icon='fa-upload',style={'font_weight':'bold'})
        self.choose_inputs = widgets.RadioButtons(
            options = options,
            layout = self.mf_layout,
        )
        self.load = widgets.VBox([self.load_button,self.choose_inputs])
        with self.out:
            clear_output()
            if self.load_inputs.value:
                display(self.load_button)
                display(self.choose_inputs)
            display(self.sheet)
        
    def _init_controls(self):
        self.save_changes.on_click(self._save_changes)
        self.load_inputs.observe(self._load_inputs,'value')
        self.load_button.on_click(self._load)
        self.revert.on_click(self._revert)
        
    def _revert(self, sender):
        self.sheet = self._sheet_from_fpth(self.fpth_inputs)
        with self.out:
            clear_output()
            display(self.sheet)
        
        
    def _save_changes(self, sender):
        self.data_out = to_dataframe(self.sheet)
        self.data_out.to_csv(self.fpth_out)
        display(Markdown('changes saved to: {0}'.format(self.fpth_out)))
        with self.out:
            clear_output()
            if self.load_inputs.value:
                display(self.load_button)
                display(self.choose_inputs)
            dateTimeObj = datetime.now()
            timestampStr = dateTimeObj.strftime("%d-%b-%Y %H:%M:%S:")
            display(Markdown('{0} changes saved to: {1}'.format(timestampStr,self.fpth_out)))
            display(self.sheet)
        self.display()

    def _load(self,sender):
        fpth = self.choose_inputs.value
        try:
            self.iserror = False
            self.sheet = self._sheet_from_fpth(fpth)
        except:
            self.iserror = True
            self.errormessage = '''__error__ loading : {0}.   
            the file has either been deleted or modified such that it is unreadable'''.format(fpth)
        
        with self.out:
            clear_output()
            if self.load_inputs.value:
                display(self.load_button)
                display(self.choose_inputs)
            if self.iserror:
                display(Markdown(self.errormessage))
            display(self.sheet)
        self.display()
        
    def _load_inputs(self,sender):
        with self.out:
            clear_output()
            if self.load_inputs.value:
                display(self.load_button)
                display(self.choose_inputs)
            display(self.sheet)

    def get_logged_inputs(self):

        def _gettags(tags):
            if tags == 'nan':
                return 'no tags'
            else:
                return tags
        def _getissue(formalIssue):
            if formalIssue == 'nan':
                return 'no formal issue'
            else:
                return formalIssue

        df_log = del_matching(pd.read_csv(self.fpth_log),'Unnamed')
        di = {}
        for n in range(0,len(df_log)):
            #description = str(self.jobno)+ ' PROJECT FILE' + ' - ' \
            #    + str(df_log.loc[n,'processName']) + ' - ' \
            #    + str(df_log.loc[n,'datetime']) + ' - ' \
            #    + str(df_log.loc[n,'user']) + ' - ' \
            #    + _getissue(str(df_log.loc[n,'formalIssue'])) + ' - ' \
            #    + _gettags(str(df_log.loc[n,'tags']))
            description = 'PROJECT: ' + df_log.loc[n,'fpthInputs']
            di[description] = df_log.loc[n,'fpthInputs']
        return di

    def get_template_inputs(self):
        fpths = self.fpth_inputs_options['template']['fpths']
        di = {}
        for fpth in fpths:
            #description = 'MXF TEMPLATE FILE' + ' - ' \
            #    + rc.process_name + ' - ' \
            #    + time_meta_data(fpth,as_DataFrame=True)['time_of_most_recent_content_modification'][0] + ' - ' \
            #    + os.path.basename(fpth) 
            description = 'TEMPLATE: '+ fpth
            di[description] = fpth
        return di

    def display(self):
        display(self.button_bar)
        display(self.out)
        


# +
config={
    'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),
    'fdir':'.',
    }
#from pprint import pprint
#rc = RunConfig(config)
#pprint(rc.config)

e = EditRunCsv(fpth,config)
e
# +
from mf_modules.pydtype_operations import read_json, read_yaml
from shutil import copyfile

class VersionController(EditCsv):

    def __init__(self):
        self.fpth_in = fpth_in
        self.fpth_out = fpth_out
        
    @property
    def _map(self):
        return {
            '.csv':self.read_csv,
            '.json':self.read_json,
            '.yaml':self.read_yaml,
        }
    
    def read_csv(self):
        self.existing_data = pd.read_csv(self.fpth_out)
        
    def read_json(self):
        self.existing_data = read_json(self.fpth_out)
        
    def read_json(self):
        self.existing_data = read_yaml(self.fpth_out)
    
    def detect_change(self):
        if self.existing_data == self.data_out:
            self.change = True
        else:
            self.change = False
    
    def archive_file(self):
        fdir = os.path.join(os.path.dirname(self.fpth_out,'archive'))
        timestamp = str(pd.to_datetime('today'))[:-9].replace(':','').replace('-','').replace(' ','-')
        ext = os.path.splitext(self.fpth_out)[1]
        fnm = timestamp + os.path.splitext(os.path.basename(self.fpth_out))[1] + ext
        fpth = os.path.join(fdir,fnm)
        copyfile(self.fpth_out,fpth)
        

# -





    def _archive_config(self):
        # JUST NEED TO COPY AND PASTE FOMR THE fpth_inputs FOLDER!
        fdir = os.path.join(os.path.dirname(self.config['process_name']),'archive')
        make_dir(fdir)
        _time = str(pd.to_datetime('today'))[:-9].replace(':','').replace('-','').replace(' ','-')
        _ext = os.path.splitext(self.config['process_name'])[1]
        fnm = _time + self.config['process_name'] + _ext
        fpth = os.path.join(fdir,fnm)
        li = [
            {
                'old_fpth': 'adf'
            }
        ]
        copy_rename(li, pr=False)



# +
#>>> from deepdiff import DeepDiff  # For Deep Difference of 2 objects
#>>> from deepdiff import grep, DeepSearch  # For finding if item exists in an object
#>>> from deepdiff import DeepHash  # For hashing objects based on their contents####
#>>> t1 = {1:1, 2:2, 3:3, 4:{"a":"hello", "b":[1, 2, 3]}}
#>>> t2 = {1:1, 2:2, 3:3, 4:{"a":"hello", "b":[1, 3, 2, 3]}}
#>>> ddiff = DeepDiff(t1, t2, ignore_order=False)
#>>> print (ddiff)
#fpth = r'C:\engDev\git_mf\ipyrun\ipyrun\appdata\inputs\inputs-eplus_pipework_params.csv'
#fpth1 = r'C:\engDev\git_mf\ipyrun\ipyrun\appdata\inputs\inputs-eplus_pipework_params-1.csv'

# +

from IPython.display import clear_output, display, Image, FileLink, FileLinks, JSON, Markdown, HTML
from markdown import markdown
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
    
class FileController():
    
    def __init__(self, fpth_inputs_options):
        self.out = widgets.Output()
        self.fpth_inputs_options = fpth_inputs_options
        self.fpth_inputs = fpth_inputs_options['working']['fpths'][0]
        self._errors()
        self.form()
        self._init_controls()
    
    @property
    def mf_layout(self):
        return widgets.Layout(
            display='flex',
            flex_flow='row',
            justify_content='flex-start',
            #border='dashed 0.2px green',
            grid_auto_columns='True',
            width='100%',
            align_items='stretch',  
        )
        
    def _errors(self):
        self.errors=[]
        self.iserror = False
        self.errormessage = 'no error'
        
    def form(self):
        
        # button bar
        self.save_changes = widgets.Button(description='save changes',button_style='success',style={'font_weight':'bold'})
        self.revert = widgets.Button(description='revert to last save',button_style='warning',style={'font_weight':'bold'})#,button_style='success'
        self.load_inputs = widgets.ToggleButton(description='inputs from file',button_style='info',style={'font_weight':'bold'})
        self.button_bar = widgets.HBox([self.save_changes, self.revert, self.load_inputs])

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
        self.inputform = _markdown(value='*TESTING*')
    
    def _init_controls(self):
        self.save_changes.on_click(self._save_changes)
        self.load_inputs.observe(self._load_inputs,'value')
        self.load_button.on_click(self._load)
        self.revert.on_click(self._revert)
        
    def _revert(self, sender):
        fpth = self.fpth_inputs
        self.inputform = _markdown(value='revert to inputs in last save of: {0}'.format(fpth))
        self.update_display()
        self.display()

    def _save_changes(self, sender):
        fpth = self.fpth_inputs
        dateTimeObj = datetime.now()
        self.save_timestampStr = dateTimeObj.strftime("%d-%b-%Y %H:%M:%S")
        self.inputform = _markdown(value='{0} saved at: {1}'.format(fpth, self.save_timestampStr))
        self.update_display()
        self.display()

    def _load(self,sender):
        self.update_display()
        self.display()
        fpth = self.choose_inputs.value
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
                display(self.load_button)
                display(self.choose_inputs)
                display(Markdown(message))
            if self.iserror:
                display(Markdown(self.errormessage))
            
    def _load_inputs(self,sender):
        self.update_display()
        self.display()
        with self.out:
            clear_output()
            if self.load_inputs.value:
                display(self.load_button)
                display(self.choose_inputs)
                
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
        self.layout = widgets.VBox([self.button_bar, self.inputform])

    def display(self):
        display(self.layout)
        display(self.out)

    def _ipython_display_(self):
        self.update_display()
        self.display()
        
        
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
            '.\\appdata\\inputs\\archive\\20200607_1420-jg-inputs-eplus_pipework_params.csv']
    },
    'working': {
        'fdir': '.\\appdata\\inputs',
        'fpths': ['.\\appdata\\inputs\\inputs-eplus_pipework_params.csv']
    },
}
d = FileController(fpth_inputs_options)
d
# -


d.update_display()
d.display()

# +
from mf_modules.datamine_functions import time_meta_data
from mf_modules.pandas_operations import del_matching


class EditRunCsv(EditCsv,RunConfig):
    
    def __init__(self, fpth_in, config, fpth_out=None):
        self.errors=[]
        self.iserror = False
        self.errormessage = 'no error'
        self.config = config
        self.user_keys = list(config.keys())
        if fpth_out==None:
            self.fpth_out = fpth_in
        else:
            self.fpth_out = fpth_out
        self.sheet = self._sheet_from_fpth(self.fpth_in)
        self.form()

        
    @property
    def mf_layout(self):
            display='flex',
            flex_flow='row',
            justify_content='flex-start',
            #border='dashed 0.2px green',
            grid_auto_columns='True',
            align_items='stretch',  
        )
        
    def form(self):
        
        # button bar
        self.save_changes = widgets.Button(description='save changes',button_style='success',style={'font_weight':'bold'})
        self.revert = widgets.Button(description='revert to last save',button_style='warning',style={'font_weight':'bold'})#,button_style='success'
        self.load_inputs = widgets.ToggleButton(description='inputs from file',button_style='info',style={'font_weight':'bold'})
        self.button_bar = widgets.HBox([self.save_changes, self.revert, self.load_inputs])
        self.layout = self.sheet
        
        # nested buttons
        template_inputs = self.get_template_inputs()
        project_inputs = self.get_logged_inputs()
        options = dict(template_inputs, **project_inputs)
        self.load_button = widgets.Button(description = 'load',icon='fa-upload',style={'font_weight':'bold'})
        self.choose_inputs = widgets.RadioButtons(
            options = options,
            layout = self.mf_layout,
        )
        self.load = widgets.VBox([self.load_button,self.choose_inputs])
        #with self.out:
        #    clear_output()
        #    if self.load_inputs.value:
        #        display(self.load_button)
        #        display(self.choose_inputs)
        #    display(self.sheet)
        
    def _init_controls(self):
        self.save_changes.on_click(self._save_changes)
        self.load_inputs.observe(self._load_inputs,'value')
        self.load_button.on_click(self._load)
        self.revert.on_click(self._revert)
        
    def _revert(self, sender):

        print('adsfasdf asd')
        self.sheet = self._sheet_from_fpth(self.fpth_inputs)
        self.layout = widgets.Label('fuck you')
        self.update_display()  
        self.display() 
        #with self.out:
        #    clear_output()
        #    display(self.sheet)

        
        
    def _save_changes(self, sender):
        self.update_display()    
        self.display()
        self.data_out = to_dataframe(self.sheet)
        self.data_out.to_csv(self.fpth_out)
        display(Markdown('changes saved to: {0}'.format(self.fpth_out)))
        with self.out:
            clear_output()
            if self.load_inputs.value:
                display(self.load_button)
                display(self.choose_inputs)
            dateTimeObj = datetime.now()
            timestampStr = dateTimeObj.strftime("%d-%b-%Y %H:%M:%S:")
            display(Markdown('{0} changes saved to: {1}'.format(timestampStr,self.fpth_out)))
            display(self.sheet)


    def _load(self,sender):
        self.update_display()
        self.display()
        fpth = self.choose_inputs.value
        try:
            self.iserror = False
            self.sheet = self._sheet_from_fpth(fpth)
        except:
            self.iserror = True
            self.errormessage = '''__error__ loading : {0}.   
            the file has either been deleted or modified such that it is unreadable'''.format(fpth)

        with self.out:
            clear_output()
            if self.load_inputs.value:
                display(self.load_button)
                display(self.choose_inputs)
            if self.iserror:
                display(Markdown(self.errormessage))
            display(self.sheet)

        
    def _load_inputs(self,sender):
        self.update_display()
        self.display()
        with self.out:
            clear_output()
            if self.load_inputs.value:
                display(self.load_button)
            #display(self.sheet)


    def get_logged_inputs(self):

        def _gettags(tags):
            if tags == 'nan':
                return 'no tags'
            else:
                return tags
        def _getissue(formalIssue):
            if formalIssue == 'nan':
                return 'no formal issue'
            else:
                return formalIssue

        df_log = del_matching(pd.read_csv(self.fpth_log),'Unnamed')
        di = {}
        for n in range(0,len(df_log)):
            #description = str(self.jobno)+ ' PROJECT FILE' + ' - ' \
            #    + str(df_log.loc[n,'processName']) + ' - ' \
            #    + str(df_log.loc[n,'datetime']) + ' - ' \
            #    + str(df_log.loc[n,'user']) + ' - ' \
            #    + _getissue(str(df_log.loc[n,'formalIssue'])) + ' - ' \
            #    + _gettags(str(df_log.loc[n,'tags']))
            description = 'PROJECT: ' + df_log.loc[n,'fpthInputs']
            di[description] = df_log.loc[n,'fpthInputs']
        return di

    def get_template_inputs(self):
        fpths = self.fpth_inputs_options['template']['fpths']
        di = {}
        for fpth in fpths:
            #description = 'MXF TEMPLATE FILE' + ' - ' \
            #    + rc.process_name + ' - ' \
            #    + time_meta_data(fpth,as_DataFrame=True)['time_of_most_recent_content_modification'][0] + ' - ' \
            #    + os.path.basename(fpth) 
            description = 'TEMPLATE: '+ fpth
            di[description] = fpth
        return di

    def update_display(self):
        print('asdf asdf')
        self.layout = widgets.VBox([self.button_bar,self.sheet])
    
    def display(self):
        #display(self.button_bar)
        display(self.layout)
        display(self.out)
  
    def _ipython_display_(self):
        self.update_display()
        self.display()
# -

e.fpth_inputs_options



# +
config={
    'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),
    'fdir':'.',
    }
#from pprint import pprint
#rc = RunConfig(config)
#pprint(rc.config)

e = EditRunCsv(fpth,config)
e
# -
e.sheet



# +
class EditCsv():

    def __init__(self, fpth_in, fpth_out=None):
        self.fpth_in = fpth_in
        if fpth_out==None:
            self.fpth_out = fpth_in
        else:
            self.fpth_out = fpth_out
        self.sheet = self._sheet_from_fpth(self.fpth_in)
        self.form()
        self._init_controls()
        self.out = widgets.Output()
        
    def form(self):
        self.save_changes = widgets.Button(description='save changes',button_style='success')
        self.button_bar = widgets.HBox([self.save_changes])
        self.layout = self.sheet
        
    def _init_controls(self):
        self.save_changes.on_click(self._save_changes)
        
    def _sheet_from_fpth(self, fpth):
        df=del_matching(pd.read_csv(fpth),'Unnamed')
        sheet = ipysheet.sheet(ipysheet.from_dataframe(df)) # initiate sheet
        return sheet
    
    def _save_changes(self, sender):
        self.data_out = to_dataframe(self.sheet)
        self.data_out.to_csv(self.fpth_out)
        display(Markdown('changes saved to: {0}'.format(self.fpth_out)))
        with self.out:
            clear_output()
            dateTimeObj = datetime.now()
            timestampStr = dateTimeObj.strftime("%d-%b-%Y %H:%M:%S:")
            display(Markdown('{0} changes saved to: {1}'.format(timestampStr,self.fpth_out)))
        self.display()

    def display(self):
        display(self.button_bar, self.out, self.layout)
        
    def _ipython_display_(self):
        self.display() 
        
ec = EditCsv(fpth)
ec
# -

ec.sheet




# +
import ipywidgets as widgets
import logging

class OutputWidgetHandler(logging.Handler):
    """ Custom logging handler sending logs to an output widget """

    def __init__(self, *args, **kwargs):
        super(OutputWidgetHandler, self).__init__(*args, **kwargs)
        layout = {
            'width': '100%',
            'height': '160px',
            'border': '1px solid black'
        }
        self.out = widgets.Output(layout=layout)

    def emit(self, record):
        """ Overload of logging.Handler method """
        formatted_record = self.format(record)
        new_output = {
            'name': 'stdout',
            'output_type': 'stream',
            'text': formatted_record+'\n'
        }
        self.out.outputs = (new_output, ) + self.out.outputs

    def show_logs(self):
        """ Show the logs """
        display(self.out)

    def clear_logs(self):
        """ Clear the current logs """
        self.out.clear_output()


logger = logging.getLogger(__name__)
handler = OutputWidgetHandler()
handler.setFormatter(logging.Formatter('%(asctime)s  - [%(levelname)s] %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)
# -

handler.show_logs()


