"""
A script that takes details from an overheating model, 
and creates overheating tables and indoor temperature graphs of the model.
        
    Args:
        ** model_run_inputs: Set of Inputs/Assumptions for this Model

    Returns:
        **  data_directory: Folder where graphs are stored
        **  analysis_directory: Folder where overheating analysis table are stored
        
    Image:
        %mf_root%\\ipyrun\\examples\\testproject\\datadriven\\src\\create-model-run-doc.png

"""
# -*- coding: utf-8 -*-

from mf_modules.j_header import j_header
from IPython.core.display import HTML
from IPython.display import display, Image
from IPython.display import FileLink, FileLinks
from mf_modules.file_operations import path_leaf
import warnings
warnings.filterwarnings('ignore')# warnings.filterwarnings(action='once')
from ipywidgets import widgets
from IPython.display import display, HTML, clear_output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from mf_modules.jupyter_formatting import highlight_cell
from mf_modules.excel_in import ExcelIn
import os
import sys
import pandas as pd
import numpy as np
from shutil import copyfile
from mf_modules.pydtype_operations import read_json
from mf_modules.file_operations import make_dir
import datetime as dt
import re

#############################################
# HELPER FUNCTIONS
#############################################

def list_names_split_string (list_names, separator, maxsplit):
    '''
    ## given a list of names, returns list of split names ##
    
    Args:
        list_names (list): list of strings (eg. B_04_XX_041_LivingRoom)
        separator (str): separator to be used as criterion for the split (eg. '_')
        maxsplit (int): max number of items you want to split the string (eg.  4 = 'B', '04', 'XX', '041', 'LivingRoom'; 3 = 'B', '04', 'XX', '041_LivingRoom')
    Returns:
        list_split_names (list): list of split names 
    '''

    list_split_names = []

    for n in list(range(len(list_names))):
        list_split_name = list_names[n].split(separator,maxsplit)
        list_split_names.append(list_split_name)
    
    return list_split_names

def dict_from_list_ofsplit_names (list_split_names, list_of_tag_names):
    '''
    ## returns a dict of  ##
    
    Args:
        list_split_names (list): list of split names
        list_of_tag_names (list): list of tag names to be used as keys in dict
    
    Returns:
        dict_items (dict): dict of
    '''
    
    dict_items = dict()
    for i in list(range(len(list_of_tag_names))):       
        dict_items[str(list_of_tag_names[i])] = []
    
    for i, x in enumerate(list_of_tag_names):
        for n in list(range(len(list_split_names))):
            try:
                if len(list_split_names[n]) <= 1 and i+1==len(list_of_tag_names):
                    dict_items[str(x)].append(list_split_names[n][0])
                elif len(list_split_names[n]) <= 1 and i == 0:
                    raise Exception("first in list.")
                else:
                    dict_items[str(x)].append(list_split_names[n][i])
            except:
                dict_items[str(x)].append("undefined")
    
    return dict_items


def filter_df_by_list_keyvalues (df, list_keyvalues): #
    dict_keys_unique_values={}
    for i in list_keyvalues:  
        dict_keys_unique_values[str(i)] = list(df[str(i)].unique())
    #e.g.
    #dict_keys_unique_values = {'air_speed': [0,1,2,3], 'block_number': [a,b]}
    
    dict_dfs = dict()
    for i in list(range(len(list_keyvalues))):       
        dict_dfs['df_'+str(list_keyvalues[i])] = []
    #e.g.
    #dict_dfs = {'df_air_speed': [], 'df_block_number': []}
    
    for x in list_keyvalues:
        for n in list(range(len(dict_keys_unique_values[x]))):
            dfi = df[df[x] == dict_keys_unique_values[x][n]]
            if dfi.empty:
                continue
            if not dfi.empty:
                dict_dfs['df_'+str(x)].append(dfi)
        
    return dict_dfs

#############################################
# PLOTTER CLASS
#############################################

class Plotter:
    def __init__(self, results_raw_fpth, results_pretty_fpth, data_fpth, outputs, process_name):
        self.tag_names = ['block_number','level_number', 'flat_code', 'room_code', 'space_name']
        self.comparison_data = ["External temperature", "Dry Bulb Temperature"]
        self.results_raw_fpth = results_raw_fpth
        self.results_pretty_fpth = results_pretty_fpth
        self.out_data_dir = outputs['0']
        self.out_analysis_dir = outputs['1']
        self.out_raw_dir = outputs['2']
        self.process_name = process_name
        self.data_fpth = data_fpth
        self.start_day = 4848
        self.dfs={}

    def make_results_figs(self,air_speed):
        s = []
        for i in [0.1,0.2]:
            df = self.dfs[i]

            def myFun(row):
                if row['TM59 (pass/fail)'] == 'PASS':
                    return 'Full Pass'
                elif row['Criterion A (pass/fail)'] == 'fail' and row['Criterion B (pass/fail)'] == 'fail':
                    return 'Full Fail'
                elif row['Criterion A (pass/fail)'] == 'fail' :
                    return 'Criterion A Fail'  
                else:
                    return 'Criterion B Fail'

            df[i] = df.apply(lambda row: myFun(row), axis = 1) 
            
            s.append(df[i].value_counts(normalize=True)*100)
            with open("test.txt", "w") as text_file:
                print("{0}".format(s), file=text_file)
        df_out = pd.DataFrame(s).fillna(0)
        df_out.to_html('test.html')
        data = []
        for column in df_out:
            data.append(go.Bar(name=column, x=list(df_out.index) ,y=df_out[column]))
        fig = go.Figure(data=data)
        fig.update_layout(xaxis_type='category', barmode='stack')
        fig.write_image('test.jpeg')
        return

    def make_analysis_figs(self,air_speed):
        # Setup Colors
        colours = {'pass':'#b6f0b1',
                   'PASS':'#a1d99c',
                   'fail':' #f5b0b0',
                   'FAIL': '#ed8c8c'}

        cell_colour = 'white'
        header_colour = 'whiteSmoke'
        line_colour = 'gainsboro'

        # Format Table
        df = self.dfs[air_speed]
        df = df.round(2)
        vals = df.T.values.tolist()
        colour_map = lambda x: colours[x] if x in colours else cell_colour
        cell_colours = list([list(map(colour_map, i)) for i in vals])
        rows = df.shape[0]

        data = go.Table(
                header=dict(values=list(df.columns),
                            fill_color=header_colour,
                            line_color=line_colour,
                            align='left'),
                cells=dict(values=vals,
                           fill_color= cell_colours,
                           line_color=line_colour,
                           align='left')
                
        )
        
        layout = go.Layout(
            autosize=False,
            width=1500,
            height=rows*25+180, # Height based on number of rows
        )
        
        table = go.Figure(data=data, layout=layout)

        '''titleText = "TM59 Analysis, with air speed {0} m/s".format(air_speed)
        table.update_layout(
            title_text=titleText,
            title_font_size=17)'''

        # Copy Data Excel to Output Folder
        filename = os.path.join(self.out_raw_dir, self.process_name + '__rawTM59results')
        copyfile(self.results_raw_fpth, filename + '.xlsx')

        # Save Table to Output Folder
        filename = os.path.join(self.out_analysis_dir, self.process_name + '__TM59results')
        copyfile(self.results_pretty_fpth, filename + '.xlsx')
        table.write_json(filename + '.plotly')
        table.write_image(filename + '.jpeg')

    def toDate(self, num):
        date = dt.datetime.fromordinal((int) (num/24)+1)
        return date.replace(hour=num%24, year=2010)

    def make_data_figs(self):
        # Setup Colors
        exttemp_colour = "Crimson"
        benchmark_colour = "DodgerBlue"

        dfs = pd.read_excel(self.data_fpth,None)


        for sheet in dfs:
            if sheet != self.comparison_data[0]:
                df = dfs[sheet]

                # Create Valid filename from sheet name
                sheet_fname = re.sub('[^A-Za-z0-9_]+', '', sheet).lower() 

                # Standard Figure Layout
                fig_layout = {
                    "title":"Maximum {0}".format(sheet),
                    "xaxis_title":"Date",
                    "yaxis_title":"Temperature (C)",
                    "paper_bgcolor":"white",
                    "template":'plotly_white',
                    "showlegend":True,
                    "xaxis":dict(tickformat="%d %b")
                }

                for roomName in list(df)[1:]:
                    if roomName != "date" and roomName != "index":
    
                        end_day = self.start_day + (7*24) # Week Long Analysis
                        df_maxweek = df

                        # Create Date Column
                        df_maxweek['date'] = [self.toDate(x) for x in df_maxweek['index']] 

                        # Append data for analysis period
                        df_maxweek = df_maxweek[self.start_day:end_day]
                        df_exttemp = dfs[self.comparison_data[0]][self.start_day:end_day]
                        data = []
                        data.append(go.Scatter(x=df_maxweek['date'], y=df_maxweek[roomName], name=sheet,
                                        line=dict(color = benchmark_colour)))
                        data.append(go.Scatter(x=df_maxweek['date'], y=df_exttemp[self.comparison_data[1]], name=self.comparison_data[0],
                                        line=dict(color = exttemp_colour)))

                        # Write figure to file
                        fig = go.Figure(data=data)
                        fig.update_layout(fig_layout)
                        fig.update_layout(title="Maximum {0} - {1}".format(sheet, roomName))
                        room_fname = re.sub('[^A-Za-z0-9_]+', '', roomName) # Create Valid filename from room name
                        fig.write_image(os.path.join(self.out_data_dir, "{2}__{0}_{1}.jpeg".format(sheet_fname, room_fname, self.process_name)))
                        fig.write_json(os.path.join(self.out_data_dir, "{2}__{0}_{1}.plotly".format(sheet_fname, room_fname, self.process_name)))

            

    def read_data(self):

        IES_output_fpth=self.results_raw_fpth
        sheet_name_results = 'Results'
        sheet_name_project_info = 'Project info'
        dfs = {}
        print(self.results_raw_fpth)
        try:
            ## Extract info from excel
            df_ies_output = pd.read_excel(IES_output_fpth, sheet_name_results)
            df_project_info = pd.read_excel(IES_output_fpth, sheet_name_project_info)

            ## Split room names given list of tags (e.g by block, level, flat, space code, space name)
            # e.g. A_00_1A_01_DoubleBedroom => BlockNumber_Level_FlatNumber_RoomCode_RoomName
            room_names = df_ies_output['room_name']
            list_of_tag_names = ['block_number','level_number', 'flat_code', 'room_code', 'space_name']
            separator = '_'
            maxsplit = len(list_of_tag_names)
            room_names_split = list_names_split_string (room_names, separator, maxsplit)
            IES_split_names = dict_from_list_ofsplit_names (room_names_split, list_of_tag_names)

            ## Create Data Frame from Dict of Split Names 
            df_IES_split_names = pd.DataFrame.from_dict(IES_split_names)

            ## Join Output data frame with Data Frame of split names
            df_ies_output_compiled = df_ies_output.join(df_IES_split_names)

            air_speeds = df_ies_output_compiled['air_speed'].unique()

            ## Split data by unique values of given key - air speed
            df = df_ies_output_compiled
            list_keyvalues = ['air_speed']
            #df_ies_output.to_html('df_ies_output.html')
            #df_IES_split_names.to_html('df_IES_split_names.html')
            #df_ies_output_compiled.to_html('df_ies_output_compiled.html')

            dfs_filt_as = filter_df_by_list_keyvalues (df, list_keyvalues)

            ## CREATE PIVOT TABLE OF LIST OF DFs AND COLOUR BASED ON VALUES (e.g. PASS, FAIL) 
            values_pivot = 'values'
            index_pivot = list_of_tag_names
            columns_pivot = ['value_names']
            num_cols = ['Criterion A (%)', 'Criterion B (%)', 'Criterion C (%)', 'Fixed Temp Criteria (%)']
            
            for x in list(range(len(dfs_filt_as['df_air_speed']))):
                df = pd.pivot_table(dfs_filt_as['df_air_speed'][x],\
                                    values=values_pivot,\
                                    index=index_pivot,\
                                    columns=columns_pivot,\
                                    aggfunc=np.sum)

                df.reset_index(inplace=True)
                types = {col:('float' if col in num_cols else 'str') for col in df}
                df = df.astype(types) 
                for col in df:
                    if col in num_cols:
                        df = df
                
                self.dfs[list(air_speeds)[x]] = df

        except:
            import traceback
            with open("log.txt", "w") as log_file:
                traceback.print_exc(file=log_file)

        return dfs

def main(inputs, outputs, process_name):
    input_dir = os.path.dirname(inputs["Model File Path"])
    tm59_raw_fpth = ""
    tm59_pretty_fpth = ""
    tm59_mv_raw_fpth = ""
    tm59_mv_pretty_fpth = ""
    data_fpth = ""
    
    # Find model excel files
    for file in os.listdir(input_dir):
        if file.endswith(".xlsx"):
            tag = file.split("__")[0]
            path = str(os.path.join(input_dir, file))
            if tag == "data":
                data_fpth = path
            elif tag == "TM59-raw":
                tm59_raw_fpth = path
            elif tag == "TM59":
                tm59_pretty_fpth = path
            elif tag == "TM59-MV-raw":
                tm59_mv_raw_fpth = path
            elif tag == "TM59-MV":
                tm59_mv_pretty_fpth = path

    results_raw_fpth = ""
    results_pretty_fpth = "" 

    # Select different results if Mech Vent
    if inputs['Mechanically Ventilated?']:
        results_raw_fpth = tm59_mv_raw_fpth
        results_pretty_fpth = tm59_mv_pretty_fpth
    else:
        results_raw_fpth = tm59_raw_fpth
        results_pretty_fpth = tm59_pretty_fpth

    # Create Plotter
    plotter = Plotter(results_raw_fpth=results_raw_fpth, results_pretty_fpth=results_pretty_fpth, data_fpth=data_fpth, outputs=outputs, process_name=process_name)
    plotter.read_data()
    
    '''# Create Analysis Outputs
    plotter.make_analysis_figs(inputs["Air Speed"])

    # Create Data Graphs
    plotter.make_data_figs()'''

    plotter.make_results_figs(inputs["Air Speed"])
    return

script_outputs = {
    '0': {
        'fdir':'.', # relative to the location of the App / Notebook file
        'fnm': r'.',
        'description': "Folder for data output"
    },
    '1': {
        'fdir':'.', # relative to the location of the App / Notebook file
        'fnm': r'.',
        'description': "Folder for analysis output"
    },
    '2': {
        'fdir':'.', # relative to the location of the App / Notebook file
        'fnm': r'.',
        'description': "Folder for raw data"
    }
}

if __name__ == '__main__':

    fpth_config = sys.argv[1]
    fpth_inputs = sys.argv[2]  

    # get config and input data
    config = read_json(fpth_config)
    os.chdir(config['fdir']) # change the working dir to the app that is executing the script
    outputs = config['fpths_outputs']

    for output in list(outputs.values()):
        if not os.path.exists(output):
            os.makedirs(output)
    inputs = read_json(fpth_inputs)

    calc_inputs = {}

    def get_inputs(values, inputs):
        for l in values:
            if type(l['value']) is list:
                inputs = get_inputs(l['value'], inputs)
            else:
                inputs[l['name']] = l['value']
        return inputs

    calc_inputs = get_inputs(inputs, calc_inputs)
    df = pd.DataFrame(data=list(map(list, calc_inputs.items())))
    main(inputs=calc_inputs,outputs=outputs, process_name=config['process_name'])
    print('done')

