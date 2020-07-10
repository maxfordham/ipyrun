"""
Creates Model Run File

    Args:
        ** Model Run: Set of Inputs for this Model

    Returns:
        ** Filepath: Where data has been written to
        
    References:
        -   N/A

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
import plotly.figure_factory as ff
from mf_modules.jupyter_formatting import highlight_cell
from mf_modules.excel_in import ExcelIn
import os
import pandas as pd
import numpy as np
from shutil import copyfile

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

def flatten_list (main_list):
    '''
    ## flatten list ##
    
    Args: 
        main_list (ldfiist): list to be flattened 
        
    Returns:
        flatten_list (list): flattened list 
    '''
    flatten_list = [val for sublist in main_list for val in sublist]
    return flatten_list


def filter_df_by_list_keyvalues (df, list_keyvalues): #
    '''
    
    
    '''
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

class TM59Plotter:
    def __init__(self, input_fpth, output_fpth):
        self.tag_names = ['block_number','level_number', 'flat_code', 'room_code', 'space_name']
        self.input_fpth = input_fpth
        self.output_fpth = output_fpth
        self.dfs={}
    
    def agg(self,x):
        if all(type(i) == str for i in x):

            xList = x.to_list()
            if 'fail' in xList:
                return 'fail'
            elif 'FAIL' in xList:
                return 'FAIL'
            elif 'pass' in xList:
                return 'pass'
            else:
                return 'PASS'
        else:
            return np.nansum(x)
    
    def show_table(self,air_speed):
        values_pviot = 'TM59_values'
        index_pivot = self.tag_names
        columns_pivot = ['TM59_value_names']

        
        colours = {'pass':'#b6f0b1',
                   'PASS':'#a1d99c',
                   'fail':' #f5b0b0',
                   'FAIL': '#ed8c8c'}

        colour_bars = '#dce0e6'
        cell_colour = 'white'
        header_colour = 'whiteSmoke'
        line_colour = 'gainsboro'
        
        df = self.dfs[air_speed]
        df = df.round(2)
        vals = df.T.values.tolist()
        
        l = [[0.1, 'pass','FAIL',10,'A'],[0.1, 'pass','FAIL',10,'A']]
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
            height=rows*25+180,
        )
        
        table = go.Figure(data=data, layout=layout)
        titleText = "Air Speed: {0} m/s".format(air_speed)
        table.update_layout(
            title_text=titleText,
            title_font_size=17)
        table.write_image("test.jpeg")

        
    def read_data_make_summary(self):

        IES_TM59_output_fpth=self.input_fpth
        sheet_name_results = 'TM59 results'
        sheet_name_project_info = 'Project info'
        dfs = {}
        try:

            ## 1 ## extract TM59 results from xlsx
            df_tm59_ies_output = pd.read_excel(IES_TM59_output_fpth, sheet_name_results)

            ## 2 ## extract project info from xlsx
            df_project_info = pd.read_excel(IES_TM59_output_fpth, sheet_name_project_info)

            ## 3 ## split room names given list of tags (e.g by block, level, flat, space code, space name)
            # e.g. A_00_1A_01_DoubleBedroom => BlockNumber_Level_FlatNumber_RoomCode_RoomName
            # list_of_tag_names ['block_number','level_number', 'flat_code', 'room_code', 'space_name']
            room_names = df_tm59_ies_output['room_name']
            list_of_tag_names = ['block_number','level_number', 'flat_code', 'room_code', 'space_name']
            separator = '_'
            maxsplit = len(list_of_tag_names)

            room_names_split = list_names_split_string (room_names, separator, maxsplit)
            IES_split_names = dict_from_list_ofsplit_names (room_names_split, list_of_tag_names)

            ## 4 ## create data frame from dict of split names 
            df_IES_split_names = pd.DataFrame.from_dict(IES_split_names)

            ## 5 ## join TM59 output data frame with data frame of split names
            df_tm59_ies_output_compiled = df_tm59_ies_output.join(df_IES_split_names)

            ## 6 ## analysed air_speeds
            air_speeds = df_tm59_ies_output_compiled['air_speed'].unique()

            ## 7 ## create pivot table from compiled DataFrame output+split names
            output_1 = pd.pivot_table(df_tm59_ies_output_compiled,\
                                      values='TM59_values',\
                                      index = list_of_tag_names,\
                                      columns=['TM59_value_names','air_speed'],\
                                      aggfunc=np.sum).T

            ## 8 ## split data by unique values of given key - air speed
            df = df_tm59_ies_output_compiled
            list_keyvalues = ['air_speed']
            dfs_filt_as = filter_df_by_list_keyvalues (df, list_keyvalues)
            #print_summary(xl, i)


            ## 9 ## CREATE PIVOTS TABLE OF LIST OF DFs AND COLOUR BASED ON VALUES (e.g. PASS, FAIL) 
            #pivot table inputs
            values_pviot = 'TM59_values'
            index_pivot = list_of_tag_names
            columns_pivot = ['TM59_value_names']
            pf_cols = ['Criterion A (pass/fail)','Criterion B (pass/fail)', 'TM59 (pass/fail)']
            num_cols = ['Criterion A (%)', 'Criterion B (%)']
            
            for x in list(range(len(dfs_filt_as['df_air_speed']))):
                df = pd.pivot_table(dfs_filt_as['df_air_speed'][x],\
                                    values=values_pviot,\
                                    index=index_pivot,\
                                    columns=columns_pivot,\
                                    aggfunc=np.sum)#;
                df.reset_index(inplace=True)
                types = {col:('float' if col in num_cols else 'str') for col in df}
                df = df.astype(types) 
                for col in df:
                    if col in num_cols:
                        df = df
                self.dfs[list(air_speeds)[x]] = df

        except:
            print('issue with this output: {0}'.format(IES_TM59_output_fpth))

        return dfs

def main(inputs, outputs):
    plotter = TM59Plotter(input_fpth=inputs["Results File Path"], output_fpth=outputs['0'])
    plotter.read_data_make_summary()
    plotter.show_table(0.15)
    return

script_outputs = {
    '0': {
        'fdir':'.', # relative to the location of the App / Notebook file
        'fnm': r'create_model_run.plotly',
        'description': "Creates model run file."
    }
}

if __name__ == '__main__':

    print('test')
    import sys
    import os
    fpth_config = sys.argv[1]
    fpth_inputs = sys.argv[2]
    print('fpth_script]: {0}'.format(sys.argv[0]))
    print('fpth_config: {0}'.format(fpth_config))
    print('fpth_inputs: {0}'.format(fpth_inputs))
    from mf_modules.pydtype_operations import read_json
    from mf_modules.file_operations import make_dir

    # get config and input data
    # config
    print(fpth_config)
    config = read_json(fpth_config)
    os.chdir(config['fdir']) # change the working dir to the app that is executing the script
    outputs = config['fpths_outputs']
    [make_dir(fdir) for fdir in config['fdir_outputs']]
    inputs = read_json(fpth_inputs)

    # this is the only bit that will change between scripts
    calc_inputs = {}
    def f(values, inputs):
        for l in values:
            if type(l['value']) is list:
                print(l['value'])
                inputs = f(l['value'], inputs)
            else:
                inputs[l['name']] = l['value']
        return inputs

    calc_inputs = f(inputs, calc_inputs)

    with open("calc_inputs.txt", "w") as text_file:
        print("{}".format(list(map(list, [[k, v] for k, v in calc_inputs.items()]))), file=text_file)
    main(calc_inputs,outputs)
    print('done')


