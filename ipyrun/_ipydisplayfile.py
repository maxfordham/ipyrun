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
from IPython.display import display, Image, JSON, Markdown, HTML, IFrame, clear_output
import time
from ipyaggrid import Grid
import ipywidgets as widgets
from markdown import markdown
import plotly.io as pio
import copy

from mf_modules.mydocstring_display import display_module_docstring
from mf_modules.pandas_operations import del_matching
from mf_modules.jupyter_formatting import md_fromfile
from mf_modules.jupyter_formatting import display_python_file
from mf_modules.file_operations import open_file
from mf_modules.pydtype_operations import read_json, read_txt, read_yaml
from mf_modules.datamine_functions import recursive_glob
from mf_modules.excel_in import ExcelIn


# +

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

def mfexcel_display(fpth):
    """
    displays mfexcel (written using xlsx_templater) using ipyaggrid
    """
    li = mfexcel_in(fpth)
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
                 fpth=os.path.join(os.environ['mf_root'],r'ipyrun\data\eg_filetypes\eg_plotly.plotly'),
                 description=None,
                 mf_excel=True):
        self.fpth = fpth
        self.mf_excel = mf_excel
        self.ext = os.path.splitext(fpth)[1].lower()

    @property
    def _map(self):
        return {
            '.csv':self.df_prev,
            '.xlsx':self.xl_prev,
            #'.xlsx':self._open_option,
            '.json':self.json_prev,
            '.plotly':self.plotly_prev,
            '.yaml':self.yaml_prev,
            '.yml':self.yaml_prev,
            '.png':self.img_prev,
            '.jpg':self.img_prev,
            '.jpeg':self.img_prev,
            #'.obj':self.obj_prev,
            #'.txt':self.txt_prev,
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

    def _display_meta(self):
        self.text = _markdown('`{0}`'.format(self.fpth))

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

    def json_prev(self):
        self.data = read_json(self.fpth)
        display(JSON(self.data))

    def plotly_prev(self):
        """
        display a plotly json file
        """
        display(pio.read_json(self.fpth))

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

    def xl_prev(self):
        """

        """
        if self.mf_excel:
            mfexcel_display(self.fpth)
        else:
            self._open_option()


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

# +
#fpths=[os.path.join(os.environ['mf_root'],r'ipyrun\data\eg_filetypes\eg_plotly.plotly')]
#d = DisplayFiles(fpths)
#d
# -


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
    fdir = os.path.realpath(os.path.join(fdir,r'..\data\eg_filetypes'))

    fpths = recursive_glob(rootdir=fdir)

    # single file
    d0 = DisplayFile(fpths[0])
    display(Markdown('### Example0'))
    display(Markdown('''display single file'''))
    display(d0.preview_fpth())
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




