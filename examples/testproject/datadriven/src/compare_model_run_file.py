"""
Compare Model Run File

    Args:
        ** Comparison: Set of model runs to compare

    Returns:
        ** Output Directory: Where comparison graphs are written to 
        
    References:
        -   N/A

"""
# -*- coding: utf-8 -*-

from ipywidgets import widgets
from IPython.display import display, HTML, clear_output
import plotly.io as pio
import plotly.graph_objects as go
import os
import sys
import pandas as pd
import numpy as np
from shutil import copyfile
from mf_modules.pydtype_operations import read_json
from mf_modules.file_operations import make_dir
import datetime as dt

def main(inputs, outputs):
    graphs_count = {}
    graphs_tocompare = []

    for l in inputs["Comparison"]:
        for file in os.listdir(l):
            if file.endswith(".plotly"):
                if file in graphs_count:
                    graphs_count[file] += 1
                else:
                    graphs_count[file] = 1

    for graph in graphs_count:
        if graphs_count[graph] == len(inputs["Comparison"]):
            graphs_tocompare.append(graph)

    
    for filename in graphs_tocompare:
        data_raw = []
        for l in inputs["Comparison"]:
            data_raw.append((l,pio.read_json(os.path.join(l, filename))))
            
        layout = data_raw[0][1]['layout']
        data_interim = [(x[0], x[1]['data']) for x in data_raw]
        
        clear_output()
        legend_names = []
        data_out = []
        
        colors = ["lightskyblue",
                "mediumseagreen",
                "goldenrod",
                "deeppink",
                "LightGray",
                "mediumspringgreen",
                "darksalmon"]
        color_index = 0
        for dataset in data_interim:
            for scatter in dataset[1]:
                if scatter['name'] not in legend_names:
                    plot = scatter
                    if scatter['name'] != "External temperature":
                        plot['name'] = scatter['name'].split(' - ')[0] + ' - ' + os.path.basename(dataset[0])
                        plot['line']['color'] = colors[color_index]
                        color_index += 1
                        if(color_index >= (len(colors)-1)):
                            color_index = 0
                        data_out.append(plot)
                    else:
                        data_out.insert(0, plot)

                    legend_names.append(plot['name'])

        fig = go.Figure(
            data=tuple(data_out),
            layout=layout
        )
        fig.update_layout(legend=dict(
            yanchor="bottom",
            y=-0.5,
            xanchor="left",
            x=0
        ))
        fig.write_image(os.path.join(outputs['0'], os.path.splitext(filename)[0] + '_test2.png'))
        fig.write_json(os.path.join(outputs['0'], filename))
    return

script_outputs = {
    '0': {
        'fdir':'.', # relative to the location of the App / Notebook file
        'fnm': r'./modelrunoutputs/',
        'description': "Creates model run file."
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
            os.mkdir(output)
    inputs = read_json(fpth_inputs)

    calc_inputs = {}

    def get_inputs(values, inputs):

        for l in values:
            inputs[l['name']] = l['value']
        return inputs

    calc_inputs = get_inputs(inputs, calc_inputs)

    main(calc_inputs,outputs)
    print('done')

