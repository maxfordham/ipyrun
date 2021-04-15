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
import subprocess
import sys
import pandas as pd
from IPython.display import display, JSON, Markdown, HTML, IFrame, clear_output, Image
import time
from ipyaggrid import Grid
import ipywidgets as widgets
from markdown import markdown
import plotly.io as pio
import copy
from dataclasses import dataclass, asdict
from dacite import from_dict
from typing import List

#  from mf library
from xlsxtemplater import from_excel

from ipyrun.mydocstring_display import display_module_docstring
from ipyrun.utils import del_matching, md_fromfile, display_python_file, open_file, recursive_glob, time_meta_data, read_json, read_yaml, read_txt

BUTTON_WIDTH = '37px'
BUTTON_HEIGHT = '25px'

# +

def get_ext(fpth):
    """get file extension including compound json files"""
    ext = os.path.splitext(fpth)[1].lower()
    _ext = ''
    if ext =='.json':
        li_fstr = os.path.splitext(fpth)[0].lower().split('.')
        
        if len(li_fstr) > 1:
            _ext = li_fstr[-1]
    return _ext + ext

def Vega(spec):
    """
    render Vega in jupyterlab
    https://github.com/jupyterlab/jupyterlab/blob/master/examples/vega/vega-extension.ipynb
    """
    bundle = {}
    bundle['application/vnd.vega.v5+json'] = spec
    display(bundle, raw=True)

def VegaLite(spec):
    """
    render VegaLite in jupyterlab
    https://github.com/jupyterlab/jupyterlab/blob/master/examples/vega/vega-extension.ipynb
    """
    bundle = {}
    bundle['application/vnd.vegalite.v4+json'] = spec
    display(bundle, raw=True)


#  consider replacing this with beakerx
def default_ipyagrid(df,**kwargs):

    """
    returns a default ipyagrid class

    Reference:
        https://dgothrek.gitlab.io/ipyaggrid/

    Code:
        from ipyaggrid import Grid
        grid_options = {
            #'columnDefs' : column_defs,
            'enableSorting': True,
            'enableFilter': True,
            'enableColResize': True,
            'enableRangeSelection': True,
            'enableCellTextSelection':True
        }
        g = Grid(grid_data=df,
                grid_options=grid_options,
                quick_filter=True,
                theme='ag-theme-balham')
        return g
    """
    #https://dgothrek.gitlab.io/ipyaggrid/
    grid_options = {
        #'columnDefs' : column_defs,
        'enableSorting': True,
        'enableFilter': True,
        'enableColResize': True,
        'enableRangeSelection': True,
        'enableCellTextSelection':True
    }
    _kwargs = {
        'grid_data':df,
        'grid_options':grid_options,
        'show_toggle_edit':False,
        'quick_filter':True,
        'theme':'ag-theme-balham',
    }
    _kwargs.update(kwargs)  # user overides
    g = Grid(**_kwargs)
    return g

def xlsxtemplated_display(li):
    """
    displays xlsxtemplated (written using xlsxtemplater) using ipyaggrid
    """
    for l in li:
        l['grid'] = default_ipyagrid(l['df'])
        display(Markdown('### {0}'.format(l['sheet_name'])))
        display(Markdown('{0}'.format(l['description'])))
        display(l['grid'])

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


class PreviewPy():
    """
    pass the class either a filepath or an imported
    module and get a display output of the modules
    docstring with a toggle option to view the code
    """

    def __init__(self, module):
        self.input = module
        self.out = widgets.Output()
        self.fpth = self._handle_input()
        self._init_form()
        self._init_controls()
        self._show_docstring()

    def _handle_input(self):
        if str(type(self.input)) == "<class 'module'>":
            fpth = self.input.__file__
        else:
            fpth = self.input
        if os.path.splitext(fpth)[1] !='.py':
            print('{0}: not a python file'.format(fpth))
        return fpth

    def _init_form(self):
        self.show_me_the_code = widgets.ToggleButton(description='show source code',
                              tooltip='shows the raw python code in the preview window below',
                              button_style='info')
    def _init_controls(self):
        self.show_me_the_code.observe(self._show_me_the_code, 'value')

    def _show_docstring(self):
        with self.out:
            clear_output()
            display(self.show_me_the_code)
            display_module_docstring(self.fpth)

    def _show_me_the_code(self, sender):
        with self.out:
            clear_output()
            if self.show_me_the_code.value:
                display(self.show_me_the_code)
                display(display_python_file(self.fpth))
            else:
                self._show_docstring()

    def display(self):
        display(self.out)

    def _ipython_display_(self):
        self.display()

def open_ui(fpth: str)-> [widgets.Button,widgets.Button]:
    """
    creates open file and open folder buttons
    fpth used for building tooltip
    
    Args:
        fpth
    
    Returns:
        openfile
        openfolder
    """
    openfile = widgets.Button(
        layout=widgets.Layout(width=BUTTON_WIDTH, height=BUTTON_HEIGHT),
        icon='fa-file',
        tooltip='open file: {0}'.format(fpth),
        style={'font_weight': 'bold'})   #,'button_color':'white'
    openfolder = widgets.Button(
        #description='+', 
        layout=widgets.Layout(width=BUTTON_WIDTH, height=BUTTON_HEIGHT),#,height='20px'
        icon='fa-folder',
        tooltip='open folder: {0}'.format(os.path.dirname(fpth)),
        style={'font_weight': 'bold'})  #,'button_color':'white'
    return openfile, openfolder

class DisplayFile():
    """
    displays the contents of a file in the notebook.
    where this requires data to be loaded in this is stored
    as DisplayFile().data. Maps to the appropriate viewer using
    the file extension.
        self.map = {
            '.csv':self.df_prev,
            #'.xlsx':self.xl_prev,
            '.xlsx':self._open_file,
            '.json':self.json_prev,
            '.yaml':self.yaml_prev,
            '.yml':self.yaml_prev,
            '.png':self.img_prev,
            '.jpg':self.img_prev,
            '.jpeg':self.img_prev,
            #'.obj':self.obj_prev,
            #'.txt':self.txt_prev,
            '.md':self.md_prev,
            '.py':self.py_prev,
            '.pdf':self._open_file,
            '.docx':self._open_file,
        }
    """
    def __init__(self,
                 fpth=os.path.join(os.environ['MF_ROOT'],r'ipyrun\data\eg_filetypes\eg_plotly.plotly'),
                 description=None,
                 mf_excel=True #  REMOVE THIS - ADD PARAM TO XLSXWRITER PROPERTIES!!! 
                ):
        self.fpth = fpth
        self.fdir = os.path.dirname(fpth)
        self.mf_excel = mf_excel
        self.ext = os.path.splitext(fpth)[1].lower()

    @property
    def _map(self):
        return {
            '.csv':self.df_prev,
            '.xlsx':self.xl_prev,
            '.json':self.json_prev,
            '.plotly.json':self.plotlyjson_prev,
            '.vg.json':self.vegajson_prev,
            '.vl.json':self.vegalitejson_prev,
            '.ipyui.json':self.ipyuijson_prev,
            '.yaml':self.yaml_prev,
            '.yml':self.yaml_prev,
            '.png':self.img_prev,
            '.jpg':self.img_prev,
            '.jpeg':self.img_prev,
            #'.obj':self.obj_prev,
            '.txt':self.txt_prev,
            '.md':self.md_prev,
            '.py':self.py_prev,
            '.pdf':self.pdf_prev,
            '.docx':self._open_option,
        }

    def preview_fpth(self):
        self.ext_map = self._map
        if self.ext not in list(self.ext_map.keys()):
            self.ext_map[self.ext]=self._open_option
        fn = self.ext_map[self.ext]
        fn()
        
    def _open_form(self):
        self.open_file = widgets.Button(description='open file',button_style='success')
        #self.text = widgets.Text(value=self.fpth,locked=True)
        self.open_file, self.open_folder = open_ui(self.fpth)
        self.text = _markdown('`{0}`  _(no preview available for this filetype)_'.format(self.fpth))
        self.open_form = widgets.HBox([self.open_file,self.open_folder,self.text])
        
    def _init_controls(self):
        self.open_file.on_click(self._open_file)
        self.open_folder.on_click(self._open_folder)

    def _open_option(self):
        self._open_form()
        self._init_controls()
        display(self.open_form)

    def _open_file(self, sender):
        open_file(self.fpth)
        self.text.value = markdown('opening: `{0}`'.format(self.fpth))
        time.sleep(5)
        self.text.value = markdown('`{0}`'.format(self.fpth))
        
    def _open_folder(self, sender):
        open_file(self.fdir)
        self.text.value = markdown('opening: `{0}`'.format(self.fdir))
        time.sleep(5)
        self.text.value = markdown('`{0}`'.format(self.fdir))

    def pdf_prev(self):
        display(IFrame(self.fpth, width=1000, height=600))

    def df_prev(self):
        """
        previes dataframe using the awesome ipyagrid

        Reference:
            https://dgothrek.gitlab.io/ipyaggrid/
        """
        self.data = del_matching(pd.read_csv(self.fpth),'Unnamed')
        try:
            g = default_ipyagrid(self.data)
            display(g)
        except:
            display(self.data.style)

    def vegajson_prev(self):
        """display a plotly json file"""
        display(Vega(read_json(self.fpth)))

    def vegalitejson_prev(self):
        """display a plotly json file"""
        display(VegaLite(read_json(self.fpth)))

    def plotlyjson_prev(self):
        """display a plotly json file"""
        display(pio.read_json(self.fpth))

    def ipyuijson_prev(self):
        print('add here!')

    def json_prev(self):
        display(JSON(read_json(self.fpth)))

    def yaml_prev(self):
        self.data = read_yaml(self.fpth)
        display(JSON(self.data))

    def img_prev(self):
        display(Image(self.fpth))

    def md_prev(self):
        display(Markdown("`IMAGES WON'T DISPLAY UNLESS THE MARKDOWN FILE IS IN THE SAME FOLDER AS THIS JUPYTER NOTEBOOK`"))
        md_fromfile(self.fpth)

    def py_prev(self):
        """
        pass the fpth of a python file and get a
        rendered view of the code.
        """
        p = PreviewPy(self.fpth)
        display(p)

    def txt_prev(self):
        display(Markdown("```{}```".format(read_txt(self.fpth))))

    def xl_prev(self):
        """display excel. if xlsxtemplated display as Grid, otherwise as _open_option"""
        li = from_excel(fpth)
        if li is not None:
            xlsxtemplated_display(li)
        else:
            self._open_option()

# +

def preview_output_ui(output: Output):
    """
    function that builds all of the PreviewOutput ui components and outputs form
    as well as individual components of the form such that they can be given controls
    
    Args:
        output: dataclass that defines file and file attributes (see def)
    
    Returns:
        displayui
        out
        displaypreview
        displayheader
        openpreview
        openfile
        openfolder
        note
        
    """
    # buttons
    openpreview = widgets.ToggleButton(
        #description='+', 
        icon='plus', 
        layout=widgets.Layout(width=BUTTON_WIDTH, height=BUTTON_HEIGHT),
        tooltip='preview file',
        style={'font_weight': 'bold','button_color':'white'})   
    openfile, openfolder = open_ui(output.fpth)  

    # file data
    name = os.path.basename(output.fpth)
    name = widgets.HTML('<b>{0}</b>'.format(name), layout=widgets.Layout(justify_items='center'))
    time = widgets.HTML('<i>{0}</i>'.format(output.time_of_most_recent_content_modification), layout=widgets.Layout(justify_items='center'))
    note = widgets.HTML('{0}'.format(output.note), layout=widgets.Layout(justify_items='center'))
    author = widgets.HTML('{0}'.format(output.author), layout=widgets.Layout(justify_items='center'))
    
    # put content in containers
    item0 = widgets.HBox([openpreview, openfile, openfolder, name],layout=widgets.Layout(width='40%'))
    item1 = widgets.HBox([author,note, time],layout=widgets.Layout(width='60%',justify_content='space-between'))
    displayheader = widgets.HBox([item0, item1],layout=widgets.Layout(width='100%',justify_content='space-between'))
    displaypreview = DisplayFile(output.fpth, description=output.description)#.preview_fpth()
    out = widgets.Output()
    displayui = widgets.VBox([displayheader, out])
    
    return displayui, out, displaypreview, displayheader, openpreview, openfile, openfolder, note


class PreviewOutput():
    """
    class that creates a ipywidgets based ui for previewing a file in the browser
    """
    def __init__(self, output: Output, auto_open=False):
        self.output = output  # from_dict(data=asdict(output),data_class=OutputPlus)
        self._buildui()
        self._init_controls()
        if auto_open:
            self.openpreview.value = True
            #self._openpreview(None)
        
    def _buildui(self):
        self.displayui, self.out, self.displaypreview, self.displayheader, self.openpreview, self.openfile, self.openfolder, self.note = preview_output_ui(self.output)
        
    def _init_controls(self):
        self.openpreview.observe(self._openpreview, names='value')
        self.openfile.on_click(self.displaypreview._open_file)
        self.openfolder.on_click(self.displaypreview._open_folder)
        
    def _openpreview(self,onchange):
        if self.openpreview.value:
            self.openpreview.icon ='minus'
            with self.out:
                self.displaypreview.preview_fpth()
        else:
            self.openpreview.icon = 'plus'
            with self.out:
                clear_output()
                
    def display_PreviewOutput(self):
        display(self.displayui)   
            
    def _ipython_display_(self):
        self.display_PreviewOutput() 
        
class PreviewOutputs():
    """
    class that creates a ipywidgets based ui for previewing multiple files in the browser
    """
    def __init__(self, outputs: List[Outputs],auto_open=False):
        self.outputs = outputs #  [from_dict(data=asdict(o),data_class=OutputPlus) for o in outputs]
        self.auto_open=auto_open
        self._init_form()
          
    def _init_form(self):
        self.display_outputs = [PreviewOutput(o,auto_open=self.auto_open) for o in self.outputs]
        self.display_uis = [ui.displayui for ui in self.display_outputs]
        self.display_previews = widgets.VBox(self.display_uis,layout=widgets.Layout(height='100%',justify_items='center'))
        
    def display_PreviewOutputs(self):
        display(self.display_previews) 
        
    def _ipython_display_(self):
        self.display_PreviewOutputs()


# -

class DisplayFiles():
    def __init__(self, fpths, fpths_ignore=[], fpth_prefix=''):
        self.out = widgets.Output();
        fpths_temp = copy.deepcopy(fpths)

        if type(fpths_temp) != list:
            fpths_temp = [fpths_temp]
        else:
            fpths_temp = fpths_temp

        self.fpths = copy.deepcopy(fpths_temp)
        for fpth in fpths_temp:
            if '.' not in fpth:
                self.fpths.remove(fpth)
                self.fpths += recursive_glob(rootdir=fpth)

        fpths_temp = copy.deepcopy(self.fpths)

        for fpth in fpths_temp:
            ext = os.path.splitext(fpth)[1].lower()
            if (ext in fpths_ignore) or (ext not in DisplayFile()._map.keys()):
                self.fpths.remove(fpth)
            elif fpth_prefix:
                if not os.path.basename(fpth).startswith(fpth_prefix):
                    self.fpths.remove(fpth)

        self.fpths = list(set(self.fpths))
        self.fpths.sort()
        self.fnms = [os.path.basename(fpth) for fpth in self.fpths];
        self._init_previews()
        self._init_form()

        self._init_controls()

    def _init_previews(self):
        self.previews = [DisplayFile(fpth) for fpth in self.fpths];
        self.map_previews = dict(zip(self.fnms,self.previews))
        self.map_fpths = dict(zip(self.fnms,self.fpths))

    def _init_form(self):
        self.outputsfpth = widgets.SelectMultiple(options=self.fnms,
                                                  layout=widgets.Layout(indent=True,
                                                              width='30%',
                                                              height='auto'))
        self.show_hide = widgets.ToggleButton(description='display/hide files',
                              tooltip='shows and hides display outputs of the files selected in the SelectMultiple dropdown menu',
                              button_style='success')
        self.ui = widgets.VBox([self.show_hide,
                      self.outputsfpth,
                      self.out])

    def _init_controls(self):
        self.show_hide.observe(self._show_hide, 'value')
        self.outputsfpth.observe(self._show_hide, 'value')

    def display_previews(self):
        #print(self.outputsfpth.value)
        display(Markdown(''))
        for file in self.outputsfpth.value:
            display(Markdown('#### {0}'.format(os.path.splitext(os.path.basename(file))[0])))
            s = str(self.map_previews[file]._map[self.map_previews[file].ext])
            if 'DisplayFile._open_option' not in s:
                display(Markdown('`{0}`'.format(self.map_fpths[file])))
            self.map_previews[file].preview_fpth()

    def _show_hide(self, sender):
        with self.out:
            clear_output()
            if self.show_hide.value:
                self.display_previews()
            else:
                pass

    def display(self):
        display(self.ui)
        #display(self.outputsfpth)
        #display(self.out)

    def _ipython_display_(self):
        self.display()


if __name__ =='__main__':
    # NOTE FOR FUTURE:
    # the below can be used to make documentation that looks at all functions or classes
    # rather than only the module level docstring. this would be an update to the PreviewPy class
    # +
    from inspect import getmembers, isfunction, isclass
    from mf_modules import mydocstring_display

    functions_list = [o for o in getmembers(mydocstring_display) if isfunction(o[1])]
    class_list = [o for o in getmembers(mydocstring_display) if isclass(o[1])]
    #functions_list
    #class_list
    # -

    fdir = os.path.dirname(os.path.realpath('__file__'))
    rel = os.path.join('..','data','eg_filetypes')
    fdir = os.path.realpath(os.path.join(fdir,rel))

    fpths = recursive_glob(rootdir=fdir)

    # single file
    d0 = DisplayFile(fpths[0])
    display(Markdown('### Example0'))
    display(Markdown('''display single file'''))
    display(d0.preview_fpth())
    display(Markdown('---'))
    display(Markdown(''))
    
    # single file
    o0 = Output(fpth=fpths[0])
    p0 = PreviewOutput(o0)
    display(Markdown('### Example0'))
    display(Markdown('''display single Output'''))
    display(p0)
    display(Markdown('---'))
    display(Markdown(''))

    # multiple file
    d1 = DisplayFiles(fpths)
    display(Markdown('### Example1'))
    display(Markdown('''display single file'''))
    display(d1)
    display(Markdown('---'))
    display(Markdown(''))

    fdir_eg = os.path.realpath(os.path.join(fdir,'eg_dir'))
    d2= DisplayFiles(fdir_eg)
    display(Markdown('### Example3'))
    display(Markdown('''display eg directory'''))
    display(d2)

    fdir_eg = os.path.realpath(os.path.join(fdir,'eg_dir'))
    d3 = DisplayFiles(fdir_eg, fpths_ignore=['.png'], fpth_prefix='eg')
    display(Markdown('### Example4'))
    display(Markdown('''example, with fpths_ignore and fpth_prefix'''))
    display(d3)


