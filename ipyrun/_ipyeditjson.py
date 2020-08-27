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
import pandas as pd
from IPython.display import display, Image, JSON, Markdown, HTML, display_pdf, clear_output
from markdown import markdown
from datetime import datetime

# widget stuff
import ipywidgets as widgets
import ipysheet
from ipysheet import from_dataframe, to_dataframe
from ipyfilechooser import FileChooser

# core mf_modules
from mf_modules.pydtype_operations import read_json, write_json 
from mf_modules.file_operations import make_dir


# from this repo
# this is an unpleasant hack. should aim to find a better solution
try:
    from ipyrun._filecontroller import FileConfigController, SelectEditSaveMfJson
    from ipyrun._runconfig import RunConfig
    from ipyrun._ipydisplayfile import DisplayFile, DisplayFiles, default_ipyagrid
except:
    from _filecontroller import FileConfigController, SelectEditSaveMfJson
    from _runconfig import RunConfig
    from _ipydisplayfile import DisplayFile, DisplayFiles, default_ipyagrid


# -

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


class EditDictData():
    """
    contains form layout specs and mapping dict used for associating input
    variables to the appropriate widget. 
    """
           
    @property
    def MF_FORM_ITEM_LAYOUT(self):
        return widgets.Layout(
            display='flex',
            flex_flow='row',
            justify_content='flex-start',
            #border='solid 1px green',
            grid_auto_columns='True',
            width='80%',
            align_items='stretch',  
            margin='0px 0px 0px 0px'
        )
    
    @property
    def MF_FORM_ITEM_LAYOUT1(self):
        return widgets.Layout(
            display='flex',
            flex_flow='row',
            justify_content='flex-end',
            #border='solid 1px green',
            grid_auto_columns='True',
            width='90%',
            align_items='stretch',  
            margin='0px 0px 0px 0px'
        )
    
    @property
    def MF_FORM_ITEM_LAYOUT2(self):
        return widgets.Layout(
            display='flex',
            flex_flow='row',
            justify_content='flex-start',
            align_content='flex-start',
            border='dashed 0.2px green',
            grid_auto_columns='True',
            width='100%',
            align_items='flex-start',  
        )
    
    @property
    def map_keys(self):
        return ['value', 'options', 'min', 'max']
    
    @property
    def map_widgets(self):
        # mapping dict used to guess what widget to apply
        
        try: 
            # if its already been defined return the as defined value
            # this allows for self.map_widgets_di to be extended more easily
            return self.map_widgets_di
        except:
            self.map_widgets_di = {
                'FloatText': {
                    'value_type': "<class 'float'>",
                    'options_type': "<class 'NoneType'>",
                    'min_type': "<class 'NoneType'>",
                    'max_type': "<class 'NoneType'>"
                },
               'FloatSlider': {
                    'value_type': "<class 'float'>",
                    'options_type': "<class 'NoneType'>",
                    'min_type': "<class 'float'>",
                    'max_type': "<class 'float'>"
               },
               'Dropdown': {
                    'value_type': 'any',
                    'options_type': "<class 'list'>",
                    'min_type': "<class 'NoneType'>",
                    'max_type': "<class 'NoneType'>"
               },
               'SelectMultiple': {
                    'value_type': "<class 'list'>",
                    'options_type': "<class 'list'>",
                    'min_type': "<class 'NoneType'>",
                    'max_type': "<class 'NoneType'>"
               },
               'Checkbox': {
                    'value_type': "<class 'bool'>",
                    'options_type': "<class 'NoneType'>",
                    'min_type': "<class 'NoneType'>",
                    'max_type': "<class 'NoneType'>"
               },
               'Text': {
                    'value_type': "<class 'str'>",
                    'options_type': "<class 'NoneType'>",
                    'min_type': "<class 'NoneType'>",
                    'max_type': "<class 'NoneType'>"
               },
               '_recursive_guess': {
                    'value_type': "<class 'list'>",
                    'options_type': "<class 'NoneType'>",
                    'min_type': "<class 'NoneType'>",
                    'max_type': "<class 'NoneType'>"
               }
            }
            return self.map_widgets_di
    
    @property
    def widget_lkup(self):
        try: 
            # if its already been defined return the as defined value
            # this allows for self.widget_lkup_di to be extended more easily
            return self.widget_lkup_di
        except:
            self.standard_widgets =  {
                'FloatText':widgets.FloatText,
                'FloatSlider':widgets.FloatSlider,
                'Dropdown':widgets.Dropdown,
                'Combobox':widgets.Combobox,
                'SelectMultiple':widgets.SelectMultiple,
                'Checkbox':widgets.Checkbox,
                'Text':widgets.Text,
                'Textarea':widgets.Textarea}

            self.mfcustom_widgets = {
                'DerivedText':self._derived_text,
                'DatePicker':self._date_picker,
                '_recursive_guess':self._recursive_guess,
                'ipysheet':self._ipysheet,
                'ipyagrid':self._ipyagrid,
                'FileChooser':self._file_chooser
            }
            
            self.widget_lkup_di = dict(self.standard_widgets, **self.mfcustom_widgets)
            return self.widget_lkup_di
        
    @property   
    def dont_watch(self):
        """won't called _init_controls function that watches when the 'value' of 'di' in an EditDict instance changes"""
        standard = list(self.standard_widgets.keys()) + list(self.mfcustom_widgets.keys())
        dont = ['_recursive_guess','ipysheet','ipyagrid']
        if self.widget_name not in standard:
            # don't watch cust widgets as standard
            dont.append(self.widget_name)
        return dont
        

    
class EditDict(EditDictData):
    '''
    a class that is passed a dict and then guesses the most appropriate 
    widget from the values in the dict.
    - if a nested list of dicts is passed:
        => it will create an embedded, clickable show/hide nested input form
    - if a json dataframe object is passed as the "value" and and the key:value
      "widget":"ipysheet" is passed in the same dict:
        => it will create an editable ipysheet dataframe widget
    Example:
        di = {
        'name':'name',
        'value':'value',
        'label':'label'
        }
        EditDict(di)
    '''
    def __init__(self, di):
        self.out = widgets.Output()
        self.di = di
        self.nested_g = None
        self.form()
 
    def form(self):
        self.di = self._update_di()
        if 'widget' not in self.di.keys():
            # if widget type isn't defined then the code will make a best guess
            self.di_types = self._get_var_types()
            self.widget_name, self.report = self.map_widget()           
        else:
            # otherwise it will revert to the user defined value
            self.widget_name = self.di['widget']
        self.kwargs = self._kwargfilt()
        self.layout = self._build_widget()
        
        # UPDATE THIS - LIST OF WIDGETS NOT TO WATCH
        if self.widget_name not in self.dont_watch:
            self._init_controls()
            
    def _kwargfilt(self):
        """
        widget, name, label, fpth_help are NOT passed as kwargs when building the widget. 
        all others are. 
        """
        return {k:v for (k,v) in self.di.items() if k != 'widget' and k != 'name' and k != 'label' and k != 'fpth_help' and v is not None}
    
    def _build_widget(self):
        
        if self.widget_name in list(self.widget_lkup.keys()):
            if str(type(self.widget_lkup[self.widget_name]))=="<class 'method'>":
                # then it is a developer defined custom widget that requires a class method to define
                self.widget_lkup[self.widget_name]()

            else:
                # it is a vanilla widget 
                self.widget_only = self.widget_lkup[self.widget_name](**self.kwargs)
        else:
            # it is a user defined widget
            self.widget_only = self.widget_name(**self.kwargs)

        self.widget_simple = widgets.HBox([self.widget_only,_markdown(self.di['label'])],layout=self.MF_FORM_ITEM_LAYOUT)
        self.widget_row = widgets.HBox([_markdown(self.di['name']),self.widget_simple],layout=self.MF_FORM_ITEM_LAYOUT1)
        if 'fpth_help' in self.di.keys():
            self.guide = widgets.ToggleButton(icon='fa-question-circle',
                                              description='help',
                                              tooltip='gives guidance',
                                              style={'font_weight':'bold'},
                                              layout=widgets.Layout(width='5%'))
            self.guide.observe(self._guide, 'value')
            layout = widgets.HBox([self.widget_row ,self.guide],layout=self.MF_FORM_ITEM_LAYOUT2)
        else:
            layout = widgets.HBox([self.widget_row],layout=self.MF_FORM_ITEM_LAYOUT2)
        return layout
    
    def _init_controls(self):   
        if(self.widget_name == "FileChooser"):
            self.widget_only.children[0].register_callback(self._update_change)
        else:
            self.widget_only.observe(self._update_change, 'value') 

    def _update_change(self, change):
        value = None
        if(self.widget_name == "DatePicker"):
            value = self.widget_only.value.strftime('%Y-%m-%d')
        elif(self.widget_name == "FileChooser"):
            value = self.widget_only.children[0].selected
        else:
            value = self.widget_only.value
        self.di['value'] = value

    def _guide(self, sender):
        with self.out:
            if self.guide.value:  
                if self.di['fpth_help']==list:
                    d = DisplayFiles(self.di['fpth_help'])
                    #display(Image(os.path.join(os.environ['mf_root'],r'engDevSetup\dev\icons\icon_png\help-icon.png')));
                    display(d)
                else:
                    d = DisplayFile(self.di['fpth_help'])
                    display(d.preview_fpth())
            else:
                clear_output()
                
    def _update_di(self):

        def add_to_dict(di, keyname='None', valuename=None):
            if keyname not in di.keys():
                di[keyname]=valuename
            return di
        tmp = self.di
        tmp = add_to_dict(tmp,keyname='min')
        tmp = add_to_dict(tmp,keyname='max')
        tmp = add_to_dict(tmp,keyname='options')
        tmp = add_to_dict(tmp,keyname='name', valuename='name')
        tmp = add_to_dict(tmp,keyname='label', valuename='label')
        return tmp
        
    def _get_var_types(self):

        def int_type_to_float(di):
            di_ = {}
            for key, val in di.items():
                if val == "<class 'int'>":
                    di_[key] = "<class 'float'>"
                else:
                    di_[key] = val
            return di_
        di = self.di
        keys = self.map_keys
        di_filt = { key: di[key] for key in keys }
        di_types = {key+'_type': str(type(di_filt[key])) for key in keys}
        di_types= int_type_to_float(di_types)
        return di_types
    
    def map_widget(self):
        """
        uses the types of the different inputs to map an input 
        to the appropriate widget

        Reference:
            |                 | value_type      | options_type       | min_type           | max_type           |
            |:----------------|:----------------|:-------------------|:-------------------|:-------------------|
            | FloatText       | <class 'float'> | <class 'NoneType'> | <class 'NoneType'> | <class 'NoneType'> |
            | FloatSlider     | <class 'float'> | <class 'NoneType'> | <class 'float'>    | <class 'float'>    |
            | Dropdown        | <class 'float'> | <class 'list'>     | <class 'NoneType'> | <class 'NoneType'> |
            | SelectMultiple  | <class 'list'>  | <class 'list'>     | <class 'NoneType'> | <class 'NoneType'> |
            | Checkbox        | <class 'bool'>  | <class 'NoneType'> | <class 'NoneType'> | <class 'NoneType'> |
            | Text            | <class 'str'>   | <class 'NoneType'> | <class 'NoneType'> | <class 'NoneType'> |
            | _recursive_guess| <class 'list'>  | <class 'NoneType'> | <class 'NoneType'> | <class 'NoneType'> |
        """
        di_types = self.di_types
        map_widgets = self.map_widgets
        m = 0
        for k, v in map_widgets.items():
            # this settles ambiguity for value type from Dropdown (which could be anything)
            #if k == widgets.Dropdown and di_types['value_type'] != "<class 'list'>":
            if k == 'Dropdown' and di_types['value_type'] != "<class 'list'>":
                v['value_type'] = di_types['value_type']
            if v == di_types:
                m=+1
                widget_name = k
        if m < 1:
            report = 'no matching widget found... check inputs...'
            print(di_types)
            print(report)
            widget_name = 'Text'
        elif m == 1:
            report = 'perfect match!'
        else:
            report = 'multiple matches found... check code...'
            print(di_types)
            print(report)
        return widget_name, report
    
    # -------------------------------------------------------------------------     
    # code that allows for embedded list of dicts -----------------------------
    def _recursive_guess(self):
        self.kwargs = {k:v for (k,v) in self.kwargs.items() if k != 'value'}
        self.kwargs['icon'] = 'arrow-down'
        self.widget_only = widgets.ToggleButton(**self.kwargs)
        self._recursive_controls()
        
    def _recursive_controls(self):
        self.widget_only.observe(self._call_GuessWidget, 'value')

    def _call_GuessWidget(self, sender):
        self.nested_g = EditListOfDicts(self.di['value'])
        self.di['value'] = self.nested_g.li
        with self.out:
            if self.widget_only.value:  
                display(self.nested_g)
            else:
                clear_output()
    # --------------------------------------------------------------------------
    # code that allows for embedded ipysheets ----------------------------------
    def _ipysheet(self):
        self.kwargs = {k:v for (k,v) in self.kwargs.items() if k != 'value'}
        self.kwargs['icon'] = 'arrow-down'
        self.widget_only = widgets.ToggleButton(**self.kwargs)
        self.save_ipysheet = widgets.Button(description='save')
        self._ipysheet_controls()
        
    def _ipysheet_controls(self):
        self.widget_only.observe(self.call_ipysheet, 'value')
        self.save_ipysheet.on_click(self._save_ipysheet)
        
    def call_ipysheet(self, sender):
        tmp = pd.read_json(self.di['value'])
        self.sheet = ipysheet.sheet(ipysheet.from_dataframe(tmp)) # initiate sheet
        with self.out:
            if self.widget_only.value:  
                display(self.save_ipysheet)
                display(self.sheet)
            else:
                clear_output()
    
    def _save_ipysheet(self, change):
        tmp = to_dataframe(self.sheet)
        self.di['value'] = tmp.to_json()
        with self.out:
            clear_output()
            dateTimeObj = datetime.now()
            timestampStr = dateTimeObj.strftime("%d-%b-%Y %H:%M:%S:")
            display(Markdown('{0} changes to sheet saved. hit save in main dialog to save to file'.format(timestampStr)))
        self.display()
    # --------------------------------------------------------------------------
    
    # --------------------------------------------------------------------------
    # code that allows for embedded ipysheets ----------------------------------
    def _ipyagrid(self):
        self.kwargs = {k:v for (k,v) in self.kwargs.items() if k != 'value'}
        self.kwargs['icon'] = 'arrow-down'
        self.widget_only = widgets.ToggleButton(**self.kwargs)
        self.save_ipyagrid = widgets.Button(description='save')
        self._ipyagrid_controls()
        
    def _ipyagrid_controls(self):
        self.widget_only.observe(self.call_ipyagrid, 'value')
        self.save_ipyagrid.on_click(self._save_ipyagrid)
        
    def call_ipyagrid(self, sender):
        tmp = pd.read_json(self.di['value'])
        
        self.grid = default_ipyagrid(tmp,show_toggle_edit=True)
        #ipysheet.sheet(ipysheet.from_dataframe(tmp)) # initiate sheet
        with self.out:
            if self.widget_only.value:  
                display(self.save_ipyagrid)
                display(self.grid)
            else:
                clear_output()
    
    def _save_ipyagrid(self, change):
        tmp = self.grid.grid_data_out['grid']
        self.di['value'] = tmp.to_json()
        with self.out:
            clear_output()
            dateTimeObj = datetime.now()
            timestampStr = dateTimeObj.strftime("%d-%b-%Y %H:%M:%S:")
            display(Markdown('{0} changes to sheet saved. hit save in main dialog to save to file'.format(timestampStr)))
        self.display()
    # --------------------------------------------------------------------------
    
    # --------------------------------------------------------------------------
    # other custom widgets -----------------------------------------------------
    def _derived_text(self):
        self.widget_only = widgets.HTML(**self.kwargs)
        self.widget_only.layout=widgets.Layout(border='solid 1px #BBBBBB', padding='0px 10px 0px 10px')
    
    def _date_picker(self):
        value = datetime.strptime(self.kwargs['value'], '%Y-%m-%d')
        self.widget_only = widgets.DatePicker(value=value)

    def _file_chooser(self):
        
        if 'value' in self.kwargs:
            path = os.path.realpath(self.kwargs['value'])
            fc_temp = FileChooser(filename=path, select_default=True)
        else:
            fc_temp = FileChooser()
        fc_temp.use_dir_icons = True
        self.widget_only = widgets.VBox([fc_temp])
        self.widget_only.layout=widgets.Layout(border='solid 1px #BBBBBB', padding='7px 7px 7px 7px', margin='5px 0px 5px 0px')
    # --------------------------------------------------------------------------
    
    def display(self):
        display(self.layout)
        display(self.out)
         
    def _ipython_display_(self):
        self.display()    


# +
class EditListOfDicts():
    """
    builds user input form from a list of dicts by creating a 
    loop of EditDict objects.
    """
    def __init__(self, li):
        """
        class that builds a user interface based on a list of dicts, where each dict is 
        a ipywidget user interface object. The class inteprets which widget to select based on the 
        type of the value and the keys that are passed. The keys are passed to the ipywidget 
        object as **kwargs.

        Args:
            li (list): list of dicts. each dict must contain 'name', 'value' and 'label' as the 
                minimum set of keys for making a ipywidget. additional keys that are passed 
                get become **kwargs that are passed to the selected ipywidget
                
        Example:
            ```
            li = [
                    {
                        'name':'water_volume_m3',
                        'value':15,
                        'label':'total volume of water within the closed mechanical system'
                    },
                    {
                        'name':'height_difference_m',
                        'value':48,
                        'label':'difference in height between the highest and lowest points in the system'
                    },
                    {
                        'name':'eV_acceptance_fraction',
                        'value':0.3,
                        'min':0,
                        'max':1,
                        'label':'Expansion vessel acceptance factor (= additional volume / expansion vessel volume):'
                    }
                ]
            ```
            
            >>> from ipyrun._ipyeditjson import EditListOfDicts
            >>> ui = EditListOfDicts(li)
            >>> ui
            see example image above
        Images:
            %mf_root%\ipyrun\docs\images\eg_ui.PNG
        """
        self.out = widgets.Output()
        self.li = li
        self.li_apps = self._update_li()
        self.form()
        self._init_observe()
        
    def _update_li(self):
        li_apps = []
        for l in self.li:
            if list(l.keys()) == ['app','config']:
                # app to use already explicitly specified
                li_apps.append(l)     
            else:
                # assume the config got passed without the associated app
                li_apps.append({'app': EditDict, 'config': l})     
        return li_apps
    
    def form(self):
        self.widgets = []
        for l in self.li_apps:
            self.widgets.append(l['app'](l['config']))
        self._layout()
        
    def _update_label(self, index, l):
        """
        this is used for the DerivedText widget
        """
        labelVal = ""
        firstVal = True
        for opt in l.di['options']:
            try:
                
                if(index+opt < 0):
                    raise Exception("Can only get values of positive indices")

                value = self.widgets[index+opt].di["value"]

                if(value == ""):
                    value = "XX"
                
                split_val = str(value).split(".")
                if(split_val[-1] == "0" and split_val[0].isdigit()):
                    value = str(int(value)).zfill(3)

                if not firstVal:
                    labelVal += "_"

                labelVal += str(value)

                firstVal = False
            except Exception as e:
                pass
        return "{0}".format(labelVal)
    
    def _update_change(self, change):
        for index, l in enumerate(self.widgets):
            if(l.widget_name=="DerivedText"):
                l.widget_only.value = self._update_label(index, l)
    
    def _layout(self):
        self._update_change(change=None)
        self.applayout = widgets.VBox([l.layout for l in self.widgets])
        
    def _init_observe(self): 
        for l in self.widgets:
            l.widget_only.observe(self._update_change, "value") 
        
    def _lidi_display(self):
        out = [l.layout for l in self.widgets]
        self.applayout = widgets.VBox(out)
        display(self.applayout)
        for l in self.widgets:
            display(l.out)
            
    def _ipython_display_(self):
        self._lidi_display()  
        
class SimpleEditJson(EditListOfDicts):
    """
    inherits EditListOfDicts user input form and manages the reading and 
    writing the data from a JSON file. 
    """
    def __init__(self, fpth_in, fpth_out=None):
        self.out = widgets.Output()
        self.fpth_in = fpth_in
        if fpth_out==None:
            self.fpth_out = fpth_in
        else:
            self.fpth_out = fpth_out
        self.li = read_json(self.fpth_in)
        self.li_apps = self._update_li()
        self.save_changes = widgets.Button(description='save',button_style='success')
        self.form()
        self._init_observe()
        self._init_controls()
    
    def _init_controls(self):  
        self.save_changes.on_click(self._save_changes)
        
    def _save_changes(self, sender):
        self.data_out = self.li
        #try:
        write_json(self.data_out,
                   sort_keys=True,
                   indent=4,
                   fpth=self.fpth_out,
                   print_fpth=False,
                   openFile=False)
        with self.out:
            clear_output()
            dateTimeObj = datetime.now()
            timestampStr = dateTimeObj.strftime("%d-%b-%Y %H:%M:%S:")
            display(Markdown('{0} changes to sheet logged.  to: {1}'.format(timestampStr,self.fpth_out)))
            
    def display(self):
        display(self.save_changes)
        out = [l.layout for l in self.widgets]
        self.applayout = widgets.VBox(out)
        display(self.applayout)
        for l in self.widgets:
            display(l.out)
        display(self.out)
            
    def _ipython_display_(self):
        self.display()  
        
class EditJson(EditListOfDicts, FileConfigController):
    """
    inherits EditListOfDicts user input form as well FileConfigController 
    and manages the reading and writing the data from a JSON file. 
    """
    #def __init__(self, fpth, fdir='.', local_fol='_mfengdev'):
    def __init__(self, config):

        self.out = widgets.Output()
        self._errors()
        self.config = config
        self.user_keys = list(config.keys())
        self._update_config()
        self.file_control_form()
        self.li = read_json(self.fpth_inputs)
        self.li_apps = self._update_li()
        self._init_file_controller()
        self.__build_widgets()
        
        
    def __build_widgets(self):
        self.form()
        self._init_observe()
        
    def _revert(self, sender):
        """revert to last save of working inputs file"""
        fpth = self.fpth_inputs
        self.temp_message.value = markdown('revert to inputs in last save of: {0}'.format(fpth))
        
        # ADD CODE HERE TO REVERT TO LAST SAVE
        
        self.li = read_json(self.fpth_inputs)
        self._update_from_file()

        
    def _update_from_file(self):
        
        self.widgets = []
        for l in self.li:
            self.widgets.append(EditDict(l))
            
        #self.applayout.children = ()
        #self.applayout.children = self._get_apps_layout()
        #for w in self.widgets:
        #    self.applayout.children.append(w.layout)
        
    def _get_apps_layout(self):
        app_layout = []
        for w in self.widgets:
            app_layout.append(widgets.VBox([w.layout, w.out]))
        return app_layout
    
    def _save_changes(self, sender):
        """save changes to working inputs file"""
        fpth = self.fpth_inputs
        
        dateTimeObj = datetime.now()
        self.save_timestampStr = dateTimeObj.strftime("%d-%b-%Y %H:%M:%S")
        self.temp_message.value = markdown('{0} saved at: {1}'.format(fpth, self.save_timestampStr))
        self.data_out = self.li 
        # add code here to save changes to file
        write_json(self.data_out,
                   sort_keys=True,
                   indent=4,
                   fpth=fpth,
                   print_fpth=False,
                   openFile=False)
        #self.apps_layout = widgets.VBox(self._get_apps_layout())
        
    def _load_inputs(self,sender):
        """launches the inputs from file dialog"""
        self.temp_message.value = markdown('update the user input form with data from file')
        if self.load_inputs.value:
            self.inputform.children = [self.load_button, self.choose_inputs]
        else:
            self.temp_message.value = markdown('')
            self.inputform.children = []
        #self.apps_layout = widgets.VBox(self._get_apps_layout())

    def _load(self,sender):

        fpth = self.choose_inputs.value
        # add code here to load form from file
        self.li = read_json(fpth)
        self._update_from_file()
        self.temp_message.value = markdown('input form load data from: {0}'.format(fpth))
        #self.apps_layout = widgets.VBox(self._get_apps_layout())
    
    def display(self):
        box = widgets.VBox([
            self.button_bar,
            self.temp_message,
            self.inputform,
        ])
        self.layout = box
        display(self.layout)
        #out = [l.layout for l in self.widgets]
        self.apps_layout = widgets.VBox(self._get_apps_layout())
        display(self.apps_layout)
        #for l in self.widgets:
        #    display(l.out)
        display(self.out)
            
    def _ipython_display_(self):
        self.display()  
        #self._lidi_display()  
        
class EditMfJson(SelectEditSaveMfJson, EditListOfDicts):
    """
    
    """
    def __init__(self, fdir, fnm=None):
        self.out = widgets.Output()
        super().__init__(fdir, fnm=fnm)
        
    def _save_changes(self, sender):
        """save changes to working inputs file"""
        self.fpth_out = self.file_chooser.selected
        dateTimeObj = datetime.now()
        self.save_timestampStr = dateTimeObj.strftime("%d-%b-%Y %H:%M:%S")
        self.temp_message.value = markdown('{0} saved at: {1}'.format(self.fpth_out, self.save_timestampStr))
        
        # add code here to save changes to file
        self.data_out = self.li     
        write_json(self.data_out,
                   sort_keys=True,
                   indent=4,
                   fpth=self.fpth_out,
                   print_fpth=False,
                   openFile=False)
        
        #with self.out:
        #    clear_output()
        #    dateTimeObj = datetime.now()
        #    timestampStr = dateTimeObj.strftime("%d-%b-%Y %H:%M:%S:")
        #    display(Markdown('{0} changes to sheet logged.  to: {1}'.format(timestampStr,self.fpth_out)))
            
        self.update_sse_display()
        self.sse_display()
        
    def _edit_file(self, sender):
        """save changes to working inputs file"""
        if self.edit_file.value:
            fpth = self.file_chooser.selected
            self.temp_message.value = markdown('edit inputs below and save to: {0}'.format(fpth))
            if os.path.isfile(fpth):
                self.li = read_json(fpth)
                self.form()
                self._init_observe()
                
                with self.out:
                    clear_output()
                    out = [l.layout for l in self.widgets]
                    self.applayout = widgets.VBox(out)
                    display(self.applayout)
                    for l in self.widgets:
                        display(l.out)
            else:
                with self.out:
                    clear_output()
                    display(markdown('{0} not a file'.format(fpth)))

        else:
            with self.out:
                self.temp_message.value = markdown('')
                clear_output()
        # add code here to save changes to file


        self._display()
        
    def _display(self):
        self.update_sse_display()
        self.sse_display()
        display(self.out)
                    
    def _ipython_display_(self):
        self._display()

# -
if __name__ =='__main__':

    # FORM ONLY EXAMPLE
    NBFDIR = os.path.dirname(os.path.realpath('__file__'))
    fpth = os.path.join(NBFDIR,r'appdata\inputs\test.json')
    fpth = r'C:\engDev\git_mf\ipyrun\examples\notebooks\appdata\inputs\inputs-expansion_vessel_sizing.json'
    li = read_json(fpth)
    g = EditListOfDicts(li)
    display(Markdown('### Example0'))
    display(Markdown('''Edit list of dicts'''))
    display(g)
    display(Markdown('---'))  
    display(Markdown('')) 
    
    # Example1
    FDIR = os.path.dirname(os.path.realpath('__file__'))
    fpth = os.path.join(FDIR,r'appdata/inputs/test.json')
    simpleeditjson = SimpleEditJson(fpth)
    # display
    display(Markdown('### Example1'))
    display(Markdown('''Simple Edit Json'''))
    display(simpleeditjson)
    display(Markdown('---'))  
    display(Markdown('')) 
    
    # Example2
    # EDIT JSON FILE with custom config and file management
    config={
        'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\docx_to_pdf.py'),
        'fdir':'.',
        'script_outputs': {'0': {
            'fdir':'..\reports',
            'fnm': r'JupyterReportDemo.pdf',
            'description': "a pdf report from word"
                }
            }
        }
    editjson = EditJson(config)
    # display
    display(Markdown('### Example2'))
    display(Markdown('''EDIT JSON FILE with custom config and file management'''))
    display(editjson)
    display(Markdown('---'))  
    display(Markdown(''))    

    
    # Example3
    # EDIT NESTED JSON FILE with custom config and file management
    nestedconfig={
        'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\gbxml.py'),
        'fdir':'.',
        }
    editnestedjson = EditJson(nestedconfig)
    # display
    display(Markdown('### Example3'))
    display(Markdown('''EDIT NESTED JSON FILE with custom config and file management'''))
    display(editnestedjson)
    display(Markdown('---'))  
    display(Markdown('')) 

        
    # Example4
    # EDIT JSON with DatePicker and DerivedText widgets
    NBFDIR = os.path.dirname(os.path.realpath('__file__'))
    fpth = r'C:\engDev\git_mf\ipyrun\examples\scripts\template_inputs\inputs-create_model_run_file.json'
    li = read_json(fpth)
    g = EditListOfDicts(li)
    
    display(Markdown('### Example4'))
    display(Markdown('''Edit list of dicts iwth date picker and derived input'''))
    display(Markdown('''EDIT JSON with DatePicker and DerivedText widgetss'''))
    display(g)
    display(Markdown('---'))  
    display(Markdown('')) 
    
    
    # Example5
    # EDIT NESTED JSON FILE with custom config and file management
    nestedconfig={
        'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\gbxml.py'),
        'fdir':'.',
        }
    editnestedjson = EditJson(nestedconfig)
    # display
    display(Markdown('### Example5'))
    display(Markdown('''EDIT NESTED JSON FILE with custom config and file management'''))
    display(editnestedjson)
    display(Markdown('---'))  
    display(Markdown('')) 
    
    
    # Example6
    editmfjson = EditMfJson(r'appdata\inputs')
    # display
    display(Markdown('### Example6'))
    display(Markdown('''select mf json file and edit'''))
    display(editmfjson)
    display(Markdown('---'))  
    display(Markdown('')) 
    
    # Example7
    nestedconfig={
        'fpth_script':r'C:\engDev\git_mf\ipyrun\examples\scripts\file_chooser_test.py',
        'fdir':'.',
        }
    editnestedjson = EditJson(nestedconfig)
    # display
    display(Markdown('### Example7'))
    display(Markdown('''File Chooser Test'''))
    display(editnestedjson)
    display(Markdown('---'))  
    display(Markdown('')) 


