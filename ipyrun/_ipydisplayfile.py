# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.11.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
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
from dataclasses import dataclass, asdict, field
from dacite import from_dict
from typing import List, Dict, Callable, Type

#  from mf library
from xlsxtemplater import from_excel

from ipyrun.mydocstring_display import display_module_docstring
from ipyrun.utils import del_matching, md_fromfile, display_python_file, open_file, recursive_glob, time_meta_data, read_json, read_yaml, read_txt
from ipyrun._runconfig import Output, Outputs
from ipyrun.constants import BUTTON_WIDTH_MIN, BUTTON_HEIGHT_MIN, FDIR_PACKAGE

# +
#  NOT IN USE - need a way to display pdf's!
#  https://github.com/voila-dashboards/voila/issues/659

def served_pdf():
    value=r'<iframe width="500" height="600" src="https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf" frameborder="1" allowfullscreen></iframe>'
    myhtml =widgets.HTML(
        value=value,
        placeholder='Some HTML',
        description='Some HTML',
    )
    display(myhtml)
    
def local_pdf():
    value=r'<iframe width="500" height="600" src="../test_filetypes/eg_pdf.pdf" frameborder="1" allowfullscreen></iframe>'
    myhtml =widgets.HTML(
        value=value,
        placeholder='Some HTML',
        description='Some HTML',
    )
    display(myhtml)
    
def fromfile_pdf():
    value=r'<iframe width="500" height="600" src="file:///mnt/c/engDev/git_mf/ipyrun/test_filetypes/eg_pdf.pdf" frameborder="1" allowfullscreen></iframe>'
    myhtml =widgets.HTML(
        value=value,
        placeholder='Some HTML',
        description='Some HTML',
    )
    display(myhtml)

#served_pdf()
#local_pdf()
#fromfile_pdf()


# +
def mdboldstr(string, di):
    return '__{}__: {}'.format(string,di[string])

def mdnorms(di):
    return mdboldstr('JobNo', di) + ' ........ ' + mdboldstr('Date', di) + ' ........ ' + mdboldstr('Author', di)

def mdwildcars(di):
    exclude = ['sheet_name', 'xlsx_params', 'xlsx_exporter', 'JobNo', 'Date', 'Author', 'df', 'grid']
    others = {k:v for k,v in di.items() if k not in exclude}
    mdstr = ''
    for k, v in others.items():
        mdstr = mdstr + '__{}__: {}<br>'.format(k,v) 
    return mdstr

def mdheader(di):
    return '### {} \n {} <br> {}'.format(
        di['sheet_name'], mdnorms(di), mdwildcars(di)
    )

def xlsxtemplated_display(li):
    """
    displays xlsxtemplated (written using xlsxtemplater) using ipyaggrid
    """
    for l in li:
        l['grid'] = default_ipyagrid(l['df'])
        display(Markdown(mdheader(l)))
        display(l['grid'])
#  string = 'JobNo'
#  mdheader(di)


# -

def display_button_styles():
    """displays default ipywidget button styles"""
    styles = ['primary', 'success', 'info', 'warning', 'danger']
    for s in styles:
        b = widgets.ToggleButton(description=s, button_style=s)
        t = _markdown('```widgets.ToggleButton(description="{}", button_style="{}")```'.format(s,s))
        display(widgets.HBox([b,t]))


# +
def get_ext(fpth, get_compound=True):
    """get file extension including compound json files"""
    ext = os.path.splitext(fpth)[1].lower()
    _ext = ''
    if get_compound:
        li_fstr = os.path.splitext(fpth)[0].lower().split('.')
        if len(li_fstr) > 1:
            _ext = '.' + li_fstr[-1]

    return _ext + ext

def Vega(spec):
    """
    render Vega in jupyterlab
    https://github.com/jupyterlab/jupyterlab/blob/master/examples/vega/vega-extension.ipynb
    """
    bundle = {}
    bundle['application/vnd.vega.v5+json'] = spec
    display(bundle, raw=True);

def VegaLite(spec):
    """
    render VegaLite in jupyterlab
    https://github.com/jupyterlab/jupyterlab/blob/master/examples/vega/vega-extension.ipynb
    """
    bundle = {}
    bundle['application/vnd.vegalite.v4+json'] = spec
    display(bundle, raw=True);

# +


#  consider replacing this with ipydatagrid
def default_ipyagrid(df, **kwargs):

    """
    returns a default ipyagrid class

    Reference:
        https://dgothrek.gitlab.io/ipyaggrid/

    Code:
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

if __name__ == "__main__":
    df = pd.DataFrame.from_dict({'a':['a','b'],'b':['a','b']})
    default_ipyagrid(df)

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


class PreviewPy():
    """
    pass the class either a filepath or an imported
    module and get a display output of the modules
    docstring with a toggle option to view the code
    """

    def __init__(self, module, preview_script=True):
        self.input = module
        self.preview_script = preview_script
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
        if os.path.splitext(fpth)[1] != '.py':
            print('{0}: not a python file'.format(fpth))
        return fpth

    def _init_form(self):
        self.script_name = os.path.splitext(os.path.basename(self.fpth))[0]
        self.title = widgets.HTML('placeholder')
        self.show_fpth = _markdown('``` {} ```'.format(self.fpth))          
        self.show_me_the_code = widgets.ToggleButton(
                              layout=widgets.Layout(width=BUTTON_WIDTH_MIN)
        )
        self.headerbox = widgets.VBox([widgets.HBox([self.show_me_the_code, self.title]), self.show_fpth])
                               
        if self.preview_script:
            display(self.headerbox)
            
    def _init_controls(self):
        self.show_me_the_code.observe(self._show_me_the_code, 'value')
    
    def _update_title(self):
        self.title.value = '<b>{}</b>: {}'.format(self.script_name, self.description)

    def _show_docstring(self):
        self.show_me_the_code.icon='scroll'
        self.show_me_the_code.tooltip='show the raw python code'
        self.show_me_the_code.button_style='warning'
        self.description = 'script documentation'
        self._update_title()
        with self.out:
            clear_output()
            #display(self.show_me_the_code)
            display_module_docstring(self.fpth)

    def _show_me_the_code(self, sender):
        self.show_me_the_code.icon='book'
        self.show_me_the_code.tooltip='show the python script documentation'
        self.show_me_the_code.button_style='info'
        self.description = 'python script'
        self._update_title()
        with self.out:
            clear_output()
            if self.show_me_the_code.value:
                
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
        layout=widgets.Layout(width=BUTTON_WIDTH_MIN, height=BUTTON_HEIGHT_MIN),
        icon='fa-file',
        tooltip='open file: {0}'.format(fpth),
        style={'font_weight': 'bold'})   #,'button_color':'white'
    openfolder = widgets.Button(
        #description='+', 
        layout=widgets.Layout(width=BUTTON_WIDTH_MIN, height=BUTTON_HEIGHT_MIN),#,height='20px'
        icon='fa-folder',
        tooltip='open folder: {0}'.format(os.path.dirname(fpth)),
        style={'font_weight': 'bold'})  #,'button_color':'white'

    return openfile, openfolder



def pdf_prev(fpth):
    display(IFrame(fpth, width=1000, height=600))

def csv_prev(fpth):
    """
    previes dataframe using the awesome ipyagrid

    Reference:
        https://dgothrek.gitlab.io/ipyaggrid/
    """
    data = del_matching(pd.read_csv(fpth),'Unnamed')
    try:
        g = default_ipyagrid(data)
        display(g)
    except:
        display(data.style)

def vegajson_prev(fpth):
    """display a plotly json file"""
    display(Vega(read_json(fpth)))

def vegalitejson_prev(fpth):
    """display a plotly json file"""
    display(VegaLite(read_json(fpth)))

def plotlyjson_prev(fpth):
    """display a plotly json file"""
    display(pio.read_json(fpth))

def ipyuijson_prev(fpth):
    print('add here!')

def json_prev(fpth):
    display(JSON(read_json(fpth)))

def yaml_prev(fpth):
    data = read_yaml(fpth)
    display(JSON(data))

def img_prev(fpth):
    display(Image(fpth))

def md_prev(fpth):
    display(Markdown("`IMAGES WON'T DISPLAY UNLESS THE MARKDOWN FILE IS IN THE SAME FOLDER AS THIS JUPYTER NOTEBOOK`"))
    md_fromfile(fpth)

def py_prev(fpth):
    """
    pass the fpth of a python file and get a
    rendered view of the code.
    """
    p = PreviewPy(fpth)
    display(p)

def txt_prev(fpth):
    display(Markdown("```{}```".format(read_txt(fpth, read_lines=False))))

def xl_prev(fpth):
    """display excel. if xlsxtemplated display as Grid, otherwise as _open_option"""
    li = from_excel(fpth)
    if li is not None:
        xlsxtemplated_display(li)
        return True
    else:
        return False
        #self._open_option()

# + tags=[]
class DisplayFile():
    """
    displays the contents of a file in the notebook.
    """
    default_renderers = {
            '.csv': csv_prev,
            '.json': json_prev,
            '.plotly': plotlyjson_prev,
            '.plotly.json': plotlyjson_prev,
            '.vg.json': vegajson_prev,
            '.vl.json': vegalitejson_prev,
            '.ipyui.json': ipyuijson_prev,
            '.yaml': yaml_prev,
            '.yml': yaml_prev,
            '.png': img_prev,
            '.jpg': img_prev,
            '.jpeg': img_prev,
            #'.obj': obj_prev, # add ipyvolume viewer? 
            '.txt': txt_prev,
            '.md': md_prev,
            '.py': py_prev,
            '.pdf': pdf_prev,
        }
    def __init__(self,
                 fpth: str,
                 user_file_renderers: Dict[str, Callable] = None,
                ):
        """
        comes with the following default renderers:
            default_renderers = {
                    '.csv': csv_prev,
                    '.json': json_prev,
                    '.plotly': plotlyjson_prev,
                    '.plotly.json': plotlyjson_prev,
                    '.vg.json': vegajson_prev,
                    '.vl.json': vegalitejson_prev,
                    '.ipyui.json': ipyuijson_prev,
                    '.yaml': yaml_prev,
                    '.yml': yaml_prev,
                    '.png': img_prev,
                    '.jpg': img_prev,
                    '.jpeg': img_prev,
                    #'.obj': obj_prev, # add ipyvolume viewer? 
                    '.txt': txt_prev,
                    '.md': md_prev,
                    '.py': py_prev,
                    '.pdf': pdf_prev,
                }
        user_file_renderers can be passed to class provided they have the correct
        dict format:
            user_file_renderers = {'.ext': myrenderer}
        notice that the class allows for "compound" filetypes, especially useful for .json files
        if you want to display the data in a specific way. 
        
        Args:
            fpth (str): filepath to display
            user_file_renderers: Dict[str, Callable] = None : user defined file renderers to extend
                the class
                
        Usage:
            fpth = 'default_config.yaml'
            DisplayFile(fpth).preview_fpth()
        
        How to extend:
            if you want to update the class definition for a compound filetype that you have created, 
            you can do so using functools as follows:
            ```
                DisplayFile('default_config.test.yaml').preview_fpth()  # '.test.yaml' ext doesn't exist so renderer defaults to .yaml
                
                import functools
                user_file_renderers = {'.test.yaml': txt_prev}
                DisplayFile = functools.partial(DisplayFile, user_file_renderers=user_file_renderers)
                DisplayFile('default_config.test.yaml').preview_fpth()  # display yaml file as txt_prev renderer
            ```
        """
        self.fpth = fpth
        self.fdir = os.path.dirname(fpth)
        self.ext = get_ext(fpth)
        if user_file_renderers is None:
            self.user_file_renderers = {}
        else:
            self.user_file_renderers = user_file_renderers
        self.check_compound_ftype()

            
    def check_compound_ftype(self):
        if self.ext.count(".") > 1:  # check if compound filetype
            if not self.ext in self._map.keys():  # if specific compound renderer doesn't exist revert back to standard
                self.ext = '.' + self.ext.split('.')[-1]

    @property
    def _map(self):
        return {**self.default_renderers, **self.user_file_renderers, **{'.xlsx': self._xl_prev, '.docx': self._open_option}}

    def preview_fpth(self):
        self.ext_map = self._map
        if self.ext not in list(self.ext_map.keys()):
            self.ext_map[self.ext]=self._open_option
        self.fn = self.ext_map[self.ext]
        self.fn(self.fpth)
        
    def _open_form(self):
        self.open_file = widgets.Button(description='open file',button_style='success')
        #self.text = widgets.Text(value=self.fpth,locked=True)
        self.open_file, self.open_folder = open_ui(self.fpth)
        self.text = _markdown('`{0}`  _(no preview available for this filetype)_'.format(self.fpth))
        self.open_form = widgets.HBox([self.open_file,self.open_folder,self.text])
        
    def _init_controls(self):
        self.open_file.on_click(self._open_file)
        self.open_folder.on_click(self._open_folder)

    def _open_option(self, sender):
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

    def _xl_prev(self, fpth):
        xt = xl_prev(fpth)
        if not xt:
            self._open_option()


# + tags=[]

def preview_output_ui(output: Output, display_class: Type =DisplayFile):
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
        layout=widgets.Layout(width=BUTTON_WIDTH_MIN, height=BUTTON_HEIGHT_MIN),
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
    displaypreview = display_class(output.fpth)
    out = widgets.Output()
    displayui = widgets.VBox([displayheader, out])
    
    return displayui, out, displaypreview, displayheader, openpreview, openfile, openfolder, note


class PreviewOutput():
    """
    class that creates a ipywidgets based ui for previewing a file in the browser
    """
    def __init__(self, output: Output, auto_open: bool=False, display_class: Type =DisplayFile):
        self.output = output  # from_dict(data=asdict(output),data_class=OutputPlus)
        self.display_class = display_class
        self._buildui()
        self._init_controls()
        if auto_open:
            self.openpreview.value = True
            #self._openpreview(None)
        
    def _buildui(self):
        self.displayui, self.out, self.displaypreview, self.displayheader, self.openpreview, self.openfile, self.openfolder, self.note = preview_output_ui(self.output, display_class=self.display_class)
        
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
    def __init__(self, outputs: List[Output], auto_open=False, display_class: Type =DisplayFile):
        self.outputs = outputs
        self.display_class = display_class
        self.auto_open = auto_open
        self._init_form()
          
    def _init_form(self):
        self.display_outputs = [PreviewOutput(o,auto_open=self.auto_open, display_class=self.display_class) for o in self.outputs]
        self.display_uis = [ui.displayui for ui in self.display_outputs]
        self.display_previews = widgets.VBox(self.display_uis,layout=widgets.Layout(height='100%',justify_items='center'))
        
    def display_PreviewOutputs(self):
        display(self.display_previews) 
        
    def _ipython_display_(self):
        self.display_PreviewOutputs()


# + tags=[] active=""
# class DisplayFiles():
#     def __init__(self, fpths, fpths_ignore=[], fpth_prefix=''):
#         self.out = widgets.Output();
#         fpths_temp = copy.deepcopy(fpths)
#
#         if type(fpths_temp) != list:
#             fpths_temp = [fpths_temp]
#         else:
#             fpths_temp = fpths_temp
#
#         self.fpths = copy.deepcopy(fpths_temp)
#         for fpth in fpths_temp:
#             if '.' not in fpth:
#                 self.fpths.remove(fpth)
#                 self.fpths += recursive_glob(rootdir=fpth)
#
#         fpths_temp = copy.deepcopy(self.fpths)
#
#         for fpth in fpths_temp:
#             ext = os.path.splitext(fpth)[1].lower()
#             if (ext in fpths_ignore) or (ext not in DisplayFile()._map.keys()):
#                 self.fpths.remove(fpth)
#             elif fpth_prefix:
#                 if not os.path.basename(fpth).startswith(fpth_prefix):
#                     self.fpths.remove(fpth)
#
#         self.fpths = list(set(self.fpths))
#         self.fpths.sort()
#         self.fnms = [os.path.basename(fpth) for fpth in self.fpths];
#         self._init_previews()
#         self._init_form()
#         self._init_controls()
#
#     def _init_previews(self):
#         self.previews = [DisplayFile(fpth) for fpth in self.fpths];
#         self.map_previews = dict(zip(self.fnms,self.previews))
#         self.map_fpths = dict(zip(self.fnms,self.fpths))
#
#     def _init_form(self):
#         self.outputsfpth = widgets.SelectMultiple(options=self.fnms,
#                                                   layout=widgets.Layout(indent=True,
#                                                               width='30%',
#                                                               height='auto'))
#         self.show_hide = widgets.ToggleButton(description='display/hide files',
#                               tooltip='shows and hides display outputs of the files selected in the SelectMultiple dropdown menu',
#                               button_style='success')
#         self.ui = widgets.VBox([self.show_hide,
#                       self.outputsfpth,
#                       self.out])
#
#     def _init_controls(self):
#         self.show_hide.observe(self._show_hide, 'value')
#         self.outputsfpth.observe(self._show_hide, 'value')
#
#     def display_previews(self):
#         #print(self.outputsfpth.value)
#         display(Markdown(''))
#         for file in self.outputsfpth.value:
#             display(Markdown('#### {0}'.format(os.path.splitext(os.path.basename(file))[0])))
#             s = str(self.map_previews[file]._map[self.map_previews[file].ext])
#             if 'DisplayFile._open_option' not in s:
#                 display(Markdown('`{0}`'.format(self.map_fpths[file])))
#             self.map_previews[file].preview_fpth()
#
#     def _show_hide(self, sender):
#         with self.out:
#             clear_output()
#             if self.show_hide.value:
#                 self.display_previews()
#             else:
#                 pass
#
#     def display(self):
#         display(self.ui)
#         #display(self.outputsfpth)
#         #display(self.out)
#
#     def _ipython_display_(self):
#         self.display()
#         
# if __name__ =='__main__':
#     # NOT IN USE
#     # multiple file
#     d1 = DisplayFiles(fpths)
#     display(Markdown('### Example1'))
#     display(Markdown('''display single file'''))
#     display(d1)
#     display(Markdown('---'))
#     display(Markdown(''))
#
#     fdir_eg = os.path.realpath(os.path.join(fdir,'eg_dir'))
#     d2= DisplayFiles(fdir_eg)
#     display(Markdown('### Example3'))
#     display(Markdown('''display eg directory'''))
#     display(d2)
#
#     fdir_eg = os.path.realpath(os.path.join(fdir,'eg_dir'))
#     d3 = DisplayFiles(fdir_eg, fpths_ignore=['.png'], fpth_prefix='eg')
#     display(Markdown('### Example4'))
#     display(Markdown('''example, with fpths_ignore and fpth_prefix'''))
#     display(d3)
# -

if __name__ =='__main__':
    # NOTE FOR FUTURE:
    # the below can be used to make documentation that looks at all functions or classes
    # rather than only the module level docstring. this would be an update to the PreviewPy class
    # +
    #from inspect import getmembers, isfunction, isclass
    #from mf_modules import mydocstring_display

    #functions_list = [o for o in getmembers(mydocstring_display) if isfunction(o[1])]
    #class_list = [o for o in getmembers(mydocstring_display) if isclass(o[1])]
    #functions_list
    #class_list
    # -

    fdir = os.path.dirname(os.path.realpath('__file__'))
    rel = os.path.join('..','test_filetypes')
    fdir = os.path.realpath(os.path.join(fdir,rel))

    fpths = recursive_glob(rootdir=fdir)

    # single file
    d0 = DisplayFile(fpths[0])
    display(Markdown('### Example0'))
    display(Markdown('''display single file'''))
    display(d0.preview_fpth())
    display(Markdown('---'))
    display(Markdown(''))
    
    # single Output
    o0 = Output(fpth=fpths[0])
    p0 = PreviewOutput(o0)
    display(Markdown('### Example5'))
    display(Markdown('''display single Output'''))
    display(p0)
    display(Markdown('---'))
    display(Markdown(''))
    
    # multiple Outputs
    outputs = [Output(f) for f in fpths]
    p1 = PreviewOutputs(outputs)
    display(Markdown('### Example6'))
    display(Markdown('''display multiple Outputs'''))
    display(p1)
    display(Markdown('---'))
    display(Markdown(''))
