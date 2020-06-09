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
import time
from ipyaggrid import Grid
import ipywidgets as widgets
from markdown import markdown

from mf_modules.display_module_docstring import display_module_docstring
from mf_modules.pandas_operations import del_matching
from mf_modules.jupyter_formatting import md_fromfile
from mf_modules.jupyter_formatting import display_python_file
from mf_modules.file_operations import open_file
from mf_modules.pydtype_operations import read_json, read_txt, read_yaml


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
            #'.obj':self.obj_prev,
            #'.txt':self.txt_prev,
            '.md':self.md_prev,
            '.py':self.py_prev,
            '.pdf':self._open_file,
            '.docx':self._open_file,
        }
    """
    def __init__(self,fpth):
        self.fpth = fpth
        self.ext = os.path.splitext(fpth)[1].lower()
    
    @property
    def _map(self):
        return {
            '.csv':self.df_prev,
            #'.xlsx':self.xl_prev,
            '.xlsx':self._open_option,
            '.json':self.json_prev,
            '.yaml':self.yaml_prev,
            '.yml':self.yaml_prev,
            '.png':self.img_prev,
            '.jpg':self.img_prev,
            #'.obj':self.obj_prev,
            #'.txt':self.txt_prev,
            '.md':self.md_prev,
            '.py':self.py_prev,
            '.pdf':self._open_option,
            '.docx':self._open_option,
        }
    

    def preview_fpth(self): 
        self.ext_map = self._map
        if self.ext not in list(self.ext_map.keys()):
            self.ext_map[self.ext]=self._open_option           
        fn = self.ext_map[self.ext]
        fn()
        
    def _init_controls(self):
        self.open_file.on_click(self._open_file)
    
    def _open_form(self):
        self.open_file = widgets.Button(description='open file',button_style='success')
        #self.text = widgets.Text(value=self.fpth,locked=True)
        self.text = _markdown('`{0}`'.format(self.fpth))
        self.open_form = widgets.HBox([self.open_file,self.text])
        
    def _open_option(self):
        self._open_form()
        self._init_controls()
        display(self.open_form)
        
    def _open_file(self, sender):
        open_file(self.fpth)
        self.text.value = markdown('opening: `{0}`'.format(self.fpth))
        time.sleep(5)
        self.text.value = markdown('`{0}`'.format(self.fpth))
        
        
    def df_prev(self):
        """
        previes dataframe using the awesome ipyagrid
        
        Reference:
            https://dgothrek.gitlab.io/ipyaggrid/
        """
        self.data = del_matching(pd.read_csv(self.fpth),'Unnamed')
        try:
            #https://dgothrek.gitlab.io/ipyaggrid/
            grid_options = {
                #'columnDefs' : column_defs,
                'enableSorting': True,
                'enableFilter': True,
                'enableColResize': True,
                'enableRangeSelection': True,
            }
            g = Grid(grid_data=self.data,
                    grid_options=grid_options,
                    quick_filter=True,
                    theme='ag-theme-balham')
            display(g)
        except:
            display(self.data.style)
        
    def json_prev(self):
        self.data = read_json(self.fpth)
        display(JSON(self.data))
        
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
        
# -

class DisplayFiles():
    def __init__(self, fpths):
        self.out = widgets.Output();
        if type(fpths)!=list:
            self.fpths = [fpths]
        else:
            self.fpths = fpths
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
                                           layout=widgets.Layout(indent=False,
                                                      width='auto',
                                                      height='auto',
                                                      flex_flow='column'))
        self.show_hide = widgets.ToggleButton(description='display/hide files',
                              tooltip='shows and hides display outputs of the files selected in the SelectMultiple dropdown menu',
                              button_style='success')
        
    def _init_controls(self):
        self.show_hide.observe(self._show_hide, 'value')
    
    def display_previews(self):
        for file in self.outputsfpth.value:
            display(Markdown('#### {0}'.format(os.path.splitext(os.path.basename(file))[0])))
            s = str(d.map_previews[file]._map[d.map_previews[file].ext])
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
        display(self.show_hide)
        display(self.outputsfpth)
        display(self.out)
        
    def _ipython_display_(self):
        self.display() 


if __name__ =='__main__':
    fdir = os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\examples\eg_filetypes')
    from mf_modules.datamine_functions import recursive_glob
    fpths = recursive_glob(rootdir=fdir)
    
    # single file
    # d = DisplayFile(fpths[0])
    # d.preview_fpth()
    
    d = DisplayFiles(fpths[0])
    display(d)


