"""
A script that takes details from an overheating model, 
and creates overheating tables and indoor temperature graphs of the model.
        
    Args:
        ** model_run_inputs: Set of Inputs/Assumptions for this Model

    Returns:
        **  data_directory: Folder where graphs are stored
        **  analysis_directory: Folder where overheating analysis table are stored
    Image:
        %mf_root%\\ipyrun\\src\\img\\setup-model-run-doc.png

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

try:
    from ipyrun.graph_operations import full_width_graph
except:
    from graph_operations import full_width_graph

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
    def __init__(self, results_raw_fpth, results_pretty_fpth, data_fpth, outputs, analysis_name, process_name):
        self.tag_names = ['block_number','level_number', 'flat_code', 'room_code', 'space_name']
        self.comparison_data = ["External Temperature", "Dry Bulb Temperature", "Crimson"]        # Setup Colors
        self.thermperf_data = [('Operative temperature', 'Operative Temperature', 'DodgerBlue')]
        self.analysis_name = analysis_name
        self.results_raw_fpth = results_raw_fpth
        self.results_pretty_fpth = results_pretty_fpth
        self.out_data_dir = outputs['0']
        self.out_analysis_dir = outputs['1']
        self.out_raw_dir = outputs['2']
        self.process_name = process_name
        self.data_fpth = data_fpth
        self.start_day = 3984
        self.time_period = 7*24 
        self.dfs={}

    def make_tm59_overall_graphs(self):
        criterion_failing = []
        pass_percentage = {}
        pass_percentage_data = []
        criterion_failing_data = []

        settings = {
            "yaxis_title": '% of Rooms',
            "xaxis_title": 'Air Speed (m/s)', 
            "yaxis_tickformat":'%', 
            "xaxis_type":'category',
        }

        for i in self.air_speeds:
            df = self.dfs[i].copy()

            def category_filter(row):
                if row['TM59 (pass/fail)'] == 'PASS':
                    return 'Full Pass'
                elif row['Criterion A (pass/fail)'] == 'fail' and row['Criterion B (pass/fail)'] == 'fail':
                    return 'Full Fail'
                elif row['Criterion A (pass/fail)'] == 'fail' :
                    return 'Criterion A Fail'  
                else:
                    return 'Criterion B Fail'

            df[i] = df.apply(lambda row: category_filter(row), axis = 1) 
            pass_percentage[i] = len(df[df["TM59 (pass/fail)"]=='PASS'].index)/len(df.index)
            criterion_failing.append(df[i].value_counts(normalize=True))
        
        pass_percentage_data = go.Bar(x=list(pass_percentage.keys()),y=list(pass_percentage.values()))

        settings['title'] = '% of rooms failing each criteria, at different air speeds'
        filename = os.path.join(self.out_data_dir, "{0}__{1}".format(self.process_name, 'crit_category'))
        full_width_graph(data=pass_percentage_data, settings=settings, filename=filename, img=True, plotly=False)

        df_criterion_failing = pd.DataFrame(criterion_failing).fillna(0)
        for column in df_criterion_failing:
            criterion_failing_data.append(go.Bar(name=column, x=list(df_criterion_failing.index) ,y=df_criterion_failing[column]))

        settings['barmode'] = 'stack'
        settings['title'] = '% of rooms which pass analysis, at different air speeds'
        filename = os.path.join(self.out_data_dir, "{0}__{1}".format(self.process_name, 'percent_pass'))
        full_width_graph(data=criterion_failing_data, settings=settings, filename=filename, img=True, plotly=False)
        
    def make_tm59_average_graphs(self):
        layout = go.Layout(
                    xaxis_type='category',
                    yaxis_tickformat = '%',
                    xaxis_title="Air Speed (m/s)",
                    yaxis_title=self.analysis_name + ' Criteria',
                    width=800)


        bedroom_mean_A = {}
        bedroom_mean_B = {}
        nonbedroom_mean_A = {}

        for i in self.air_speeds:
            df = self.dfs[i].copy()
            bedroom_mask = (df['Criterion A (%)'].notnull() & df['Criterion B (%)'].notnull())
            non_bedroom_mask = (df['Criterion A (%)'].notnull() & df['Criterion B (%)'].isnull())

            bedroom_mean_A[i] = (df[bedroom_mask]['Criterion A (%)'].mean(axis = 0))/100
            bedroom_mean_B[i] = (df[bedroom_mask]['Criterion B (%)'].mean(axis = 0))/100
            nonbedroom_mean_A[i] = (df[non_bedroom_mask]['Criterion A (%)'].mean(axis = 0))/100

        data = []
        line=dict(
            color='black',
            width=2,
            dash='dash')
        critb_limit = go.Scatter(name='Criterion B - Upper Limit', 
                                y=[0.01,0.01], 
                                x=[list(bedroom_mean_B.keys())[0],
                                list(bedroom_mean_B.keys())[-1]], 
                                mode='lines',
                                line=line)

        line=dict(
            color='black',
            width=2)
        crita_limit = go.Scatter(name='Criterion A - Upper Limit', 
                                y=[0.03,0.03], 
                                x=[list(bedroom_mean_B.keys())[0],
                                list(bedroom_mean_B.keys())[-1]], 
                                mode='lines',
                                line=line)
                                
        data.append(go.Bar(name='Criterion A (%)', x=list(bedroom_mean_A.keys()), y=list(bedroom_mean_A.values())))
        data.append(go.Bar(name='Criterion B (%)', x=list(bedroom_mean_B.keys()), y=list(bedroom_mean_B.values())))
        data.append(critb_limit)
        data.append(crita_limit)

        settings = {
            "yaxis_title": self.analysis_name + ' Criteria',
            "xaxis_title": 'Air Speed (m/s)', 
            "yaxis_tickformat":'%', 
            "xaxis_type":'category',
        }

        settings['title'] = 'Average performance of bedroom spaces'
        filename = os.path.join(self.out_data_dir, "{0}__{1}".format(self.process_name, 'av_bedroom'))
        full_width_graph(data=data, settings=settings, filename=filename, img=True, plotly=False)

        data = []
        data.append(go.Bar(name='Criterion A (%)', x=list(nonbedroom_mean_A.keys()), y=list(nonbedroom_mean_A.values())))
        data.append(crita_limit)
        settings['title'] = 'Average performance of non-bedroom spaces'
        filename = os.path.join(self.out_data_dir, "{0}__{1}".format(self.process_name, 'av_non_bedroom'))
        full_width_graph(data=data, settings=settings, filename=filename, img=True, plotly=False)

    def make_results_graphs(self,air_speed):
        self.make_tm59_overall_graphs()
        self.make_tm59_average_graphs()
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
        df = df.fillna(0)
        df = df.round(2)
        df.drop('room_name', axis=1, inplace=True)
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
                        line_color= line_colour,
                        align='left',
                        height=30)
        )

        layout = {
            "autosize": False,
            "width": 1500, 
            "height":rows*30+100, 
            "margin":{'l': 3, 'r': 3, 't': 10, 'b': 0},
            "template": "simple_white",
            "titlefont": {"size": 24},
            "font": {"size": 18},
            "font_family": "Calibri"
        }    

        table = go.Figure(data=data, layout=layout)

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

    def make_thermperf_graph(self, dfs):
        xaxis = [self.toDate(x) for x in list(range(0, (self.time_period)))]
        end_day = self.start_day + self.time_period

        # Standard Figure Layout
        
        settings = {
            "xaxis_title":"Date",
            "yaxis_title":"Temperature (F)",
            "xaxis_tickformat": 'Day %-j, %H:00',
            "xaxis": {
                "tickmode" : "linear",
                "tick0" : xaxis[12]
            }
        }

        graph_inputs = []

        for x in self.thermperf_data:
            if x[0] in dfs:
                tmp = {}
                tmp['fname'] = re.sub('[^A-Za-z0-9_]+', '', x[1]).lower() 
                tmp['title'] = x[1]
                tmp['data'] = dfs[x[0]]
                tmp['color'] = x[2]
                graph_inputs.append(tmp)

        for roomName in list(graph_inputs[0]['data'])[1:]:
            data = []

            for input in graph_inputs:
                df_maxweek = input['data'].copy()
                df_maxweek = df_maxweek[self.start_day:end_day]
                data.append(go.Scatter(x=xaxis, y=df_maxweek[roomName], name=input['title'],
                                line=dict(width=1.5, color = input['color'])))
            
            df_comparison = dfs[self.comparison_data[0]][self.start_day:end_day]
            data.append(go.Scatter(x=xaxis, y=df_comparison[self.comparison_data[1]], name=self.comparison_data[0],
                            line=dict(width=2, color = self.comparison_data[2])))

            subtitle = "Maximum Average ({0} to {1})".format(self.toDate(self.start_day).strftime("%d %b"), self.toDate(end_day).strftime("%d %b"))
            room_fname = re.sub('[^A-Za-z0-9_]+', '', roomName) # Create Valid filename from room name
            
            settings['title'] = "{0} - {1}<br>{2}".format('Temperatures', roomName, subtitle)
            filename = os.path.join(self.out_data_dir, "{2}__{0}__{1}".format('temps', room_fname, self.process_name))
            full_width_graph(data=data, settings=settings, filename=filename, img=True, plotly=True)

    def make_data_graphs(self):
        if not self.data_fpth:
            return

        dfs = pd.read_excel(self.data_fpth,None)

        for sheet in dfs:
            if sheet == self.comparison_data[0]:
                df = dfs[sheet].copy()
                df = df.drop(columns=['index'])
                df = df.rolling(self.time_period).mean()
                self.start_day = df[self.comparison_data[1]].idxmax()

        self.make_thermperf_graph(dfs)

    def read_data(self):

        IES_output_fpth=self.results_raw_fpth
        sheet_name_results = 'Results'
        dfs = {}
        try:
            ## Extract info from excel
            df_ies_output = pd.read_excel(IES_output_fpth, sheet_name_results)
            #df_project_info = pd.read_excel(IES_output_fpth, sheet_name_project_info)
            
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
            self.air_speeds = list(air_speeds)

            ## Split data by unique values of given key - air speed
            df = df_ies_output_compiled
            list_keyvalues = ['air_speed']
            #df_ies_output.to_html('df_ies_output.html')
            #df_IES_split_names.to_html('df_IES_split_names.html')
            #df_ies_output_compiled.to_html('df_ies_output_compiled.html')

            dfs_filt_as = filter_df_by_list_keyvalues (df, list_keyvalues)

            ## CREATE PIVOT TABLE OF LIST OF DFs AND COLOUR BASED ON VALUES (e.g. PASS, FAIL) 
            values_pivot = 'values'
            index_pivot = list_of_tag_names + ['room_name']
            columns_pivot = ['value_names']
            num_cols = ['Criterion A (%)', 'Criterion B (%)', 'Criterion C (%)', 'Fixed Temp Criteria (%)']
            
            for x in list(range(len(dfs_filt_as['df_air_speed']))):
                df = pd.pivot_table(dfs_filt_as['df_air_speed'][x],\
                                    values=values_pivot,\
                                    index=index_pivot,\
                                    columns=columns_pivot,\
                                    aggfunc=np.min)
                
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
    input_dir = os.path.join(input_dir, r'mf_current')
    tm59_raw_fpth = ""
    tm59_pretty_fpth = ""
    tm59_mv_raw_fpth = ""
    tm59_mv_pretty_fpth = ""
    data_fpth = ""

    s = ''
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
    with open("log2.txt", "w") as text_file:
        print("{0}".format(input_dir), file=text_file)
    with open("log3.txt", "w") as text_file:
        print("{0}".format(input_dir), file=text_file)
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
    plotter = Plotter(results_raw_fpth=results_raw_fpth, results_pretty_fpth=results_pretty_fpth, data_fpth=data_fpth, outputs=outputs, analysis_name='TM59', process_name=process_name)
    plotter.read_data()
    
    # Create Analysis Outputs
    plotter.make_analysis_figs(inputs["Air Speed"])

    # Create Data Graphs
    plotter.make_data_graphs()
    
    plotter.make_results_graphs(inputs["Air Speed"])
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

