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
# main imports
import os
FDIR = os.path.dirname(os.path.realpath('__file__'))
import pandas as pd
from IPython.display import Markdown, clear_output, display
from markdown import markdown
from datetime import datetime
import time
from pprint import pprint

# widget stuff
import ipywidgets as widgets
from ipysheet import from_dataframe, to_dataframe
import ipysheet

from ipyrun.utils import make_dir, time_meta_data, del_matching
from ipyrun._runconfig import RunConfig, AppConfig
from ipyrun._filecontroller import FileConfigController
# -

from ipyrun.constants import BUTTON_WIDTH_MIN, BUTTON_HEIGHT_MIN


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class EditSheet():
    """
    simple ui that allows user to edit an ipysheet. the sheet updates the property ```self.df``` (pd.DataFrame) on change
    and  "+" and "-" controls allow for adding and removing rows. can't start with less rows that you begin with. 
    """
    def __init__(self, df, title='', add_remove_rows=True):
        self.df = df
        self.min_rows = len(df)
        self.title = title
        self.add_remove_rows = add_remove_rows
        self._init_sheet()
        self.form()
        self._add_remove_rows()
        self._init_controls()
        
    def _add_remove_rows(self):
        if self.add_remove_rows:
            self.button_bar.children = [self.add_row,self.remove_row]
        else:
            self.button_bar.children = []
            
    def _init_sheet(self):
        self.sheet = ipysheet.from_dataframe(self.df) # initiate sheet
        
    def form(self):
        self.add_row = widgets.Button(icon='fa-plus',tooltip='add row',button_style='success', layout=widgets.Layout(width=BUTTON_WIDTH_MIN))
        self.remove_row = widgets.Button(icon='fa-minus',tooltip='remove row',button_style='danger', layout=widgets.Layout(width=BUTTON_WIDTH_MIN))
        self.updated_time = widgets.HTML(now())
        self.html_title = widgets.HTML('<b>{}</b>'.format(self.title))
        self.button_bar = widgets.HBox([])
        self.bar = widgets.HBox([self.button_bar, self.html_title, self.updated_time], layout=widgets.Layout(display='flex',flex_flow='row',justify_content='space-between'))
        self.box = widgets.VBox([self.bar, self.sheet])
        
    def _init_controls(self):
        self.add_row.on_click(self._add_row)
        self.remove_row.on_click(self._remove_row)
        self._init_observe()
        
    def _init_observe(self):
        for cell in self.sheet.cells:
            cell.observe(self._onchange, 'value')
            
    def _update_row_headers(self):
        self.sheet.row_headers = [str(r) for r in list(range(0,self.sheet.rows))]       
        
    def _add_cells(self):
        for n in range(0,len(self.sheet.cells)):
            self.sheet.cells[n].value.append(None) # important to do it in-place otherwise creates a copy and breaks link to displayed ui
            
    def _add_row(self, sender):
        self.sheet.rows += 1
        self._update_row_headers()
        self._add_cells()
        self._onchange('change')
        self.display()
        
    def _remove_cells(self):
        for n in range(0,len(self.sheet.cells)):
            end = self.sheet.cells[n].value
            #self.sheet.cells[n].row_end -= 1
            self.sheet.cells[n].value.pop(len(end)-1) # important to do it in-place otherwise creates a copy and breaks link to displayed ui
            
    def _remove_row(self, sender):
        new = self.sheet.rows -1
        if new >= self.min_rows:
            self.sheet.rows -= 1
            self._update_row_headers()
            self._remove_cells()
            self._onchange('change')
            self.display()
        
    def _onchange(self, change):
        self.df = to_dataframe(self.sheet)
        self.updated_time.value = now() # this can be watched for changes by other widgets... 
        
    def display(self):
        display(self.box)

    def _ipython_display_(self):
        self.display()


# +
def debugsheet(sheet):
    
    def debugcells(cell):
        print('cell.value = {}'.format(str(cell.value)))  
        print('cell.row_start = {}'.format(str(cell.row_start)))
        print('cell.row_end = {}'.format(str(cell.row_end)))
        print('cell.row_end - col.row_start + 1 = {}'.format(str(cell.row_end - cell.row_start + 1)))
        print('len(cell.value) = {}'.format(len(cell.value)))
        
    print('sheet.rows = {}'.format(str(sheet.rows)))    
    [debugcells(cell) for cell in sheet.cells];
    
if __name__ =='__main__':
    df = pd.DataFrame.from_dict({'a':[0,1,2],'b':[1,2,3]})
    e = EditSheet(df, add_remove_rows=True, title='title')
    display(e)


# +
class EditCsv(EditSheet):
    """a simple csv editor that allows the user to add and remove rows from the table"""
    def __init__(self, fpth_in, fpth_out=None, title=None, add_remove_rows=True):
        self.fpth_in = fpth_in
        if fpth_out is None:
            self.fpth_out = fpth_in
        else:
            self.fpth_out = fpth_out
        if title is None:
            title = 'edit: {0}'.format(self.fpth_out)
        df = pd.read_csv(self.fpth_in)
        self._save_form()
        super().__init__(df,title=title,add_remove_rows=add_remove_rows)
        self._update_controls()
        
    def _add_remove_rows(self):
        if self.add_remove_rows:
            self.button_bar.children = [self.save, self.add_row,self.remove_row]
        else:
            self.button_bar.children = [self.save]
        
    def _save_form(self):
        self.save = widgets.Button(icon='fa-save',tooltip='add row',button_style='success', layout=widgets.Layout(width=BUTTON_WIDTH_MIN))
        #self.button_bar.children = [self.save,self.add_row,self.remove_row]
        
    def _update_controls(self):
        self.save.on_click(self._save)
        
    def _save(self, onclick):
        self.df.to_csv(self.fpth_out)
        
if __name__ =='__main__':
    df = pd.DataFrame.from_dict({'a':[0,1,2],'b':[1,2,3]})
    fpth = os.path.realpath(os.path.join(FDIR,'..','test_filetypes','eg_short_csv.csv'))
    df.to_csv(fpth, index=None)
    csv = EditCsv(fpth,add_remove_rows=False)
    display(csv)


# +
#  CURRENTLY BROKEN! 
class EditRunAppCsv(FileConfigController):
    """
    for use when csv is the argument to a script
    """
    def __init__(self,config):
        #self.config = config
        self.out = widgets.Output()
        self._init_RunConfig(config)
        self.file_control_form()
        self._init_FileController()
        self.sheet = self._sheet_from_fpth(self.fpth_inputs)
        self.display_sheet()

    def _sheet_from_fpth(self, fpth):
        df=del_matching(pd.read_csv(fpth),'Unnamed')
        #sheet = ipysheet.sheet(ipysheet.from_dataframe(df)) # initiate sheet
        sheet = EditSheet(df,add_remove_rows=False)
        return sheet

    def display_sheet(self):
        with self.out:
            clear_output()
            display(self.sheet)

    def _revert(self, sender):
        """revert to last save of working inputs file"""
        fpth = self.fpth_inputs
        self.temp_message.value = markdown('revert to inputs in last save of: {0}'.format(fpth))

        # add code here to revert to last save
        self.sheet = self._sheet_from_fpth(self.fpth_inputs)

        self.display_sheet()
        self.update_display()
        self.display()

    def _save_changes(self, sender):
        """save changes to working inputs file"""
        fpth = self.fpth_inputs
        dateTimeObj = datetime.now()
        self.save_timestampStr = dateTimeObj.strftime("%d-%b-%Y %H:%M:%S")
        self.temp_message.value = markdown('{0} saved at: {1}'.format(fpth, self.save_timestampStr))

        # add code here to save changes to file
        self.data_out = to_dataframe(self.sheet)
        self.data_out.to_csv(self.fpth_inputs)

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

        fpth = self.choose_inputs.value

        # add code here to load form from file
        self.sheet = self._sheet_from_fpth(fpth)
        self.temp_message.value = markdown('input form load data from: {0}'.format(fpth))

        self.display_sheet()
        self.update_display()
        self.display()
        
if __name__ == '__main__':
    from ipyrun.constants import FDIR_PACKAGE
    config = {
        'fdir':os.path.join(FDIR_PACKAGE,'test_appdir'),
        'fpth_script':os.path.join(FDIR_PACKAGE,'test_scripts','expansion_vessel_sizing.py'),
        'ftyp_inputs':'csv'
    }
    config = AppConfig(**config)
    from ipyrun._runconfig import AppConfig
    b = EditRunAppCsv(config)
    display(Markdown('### Example1'))
    display(Markdown('''EditCsv'''))
    display(b)
    display(Markdown('---'))
    display(Markdown(''))
