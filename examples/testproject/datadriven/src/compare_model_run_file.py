"""
A script that takes creates a set of graphs
comparing the indoor temperatures between a 
'Benchmark' option and an 'As Designed' option
        
    Args:
        ** benchmark: Name of the 'Benchmark' option
        ** as_designed: Name of the 'As Designed' option

    Returns:
        **  overheating_report: The final report, outputted as a PDF or Word document
        
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

def main(inputs, outputs, input_dir):

    # Create Dataset
    exttemp_colour = "Crimson"
    benchmark_colour = "DodgerBlue"
    asdesigned_colour = "MediumSeaGreen"
    dataset_raw = []
    dataset_raw.append((inputs["Benchmark"],"Benchmark", benchmark_colour))
    dataset_raw.append((inputs["As Designed"],"As Designed", asdesigned_colour))
    '''colors = ["Peru",
            "LightGray",
            "Turquoise",
            "darksalmon",
            "goldenrod"]
    color_index = 0
    for i in inputs["Comparison"]:
        dataset_raw.append((i,"",colors[color_index]))
        color_index += 1
        if color_index > len(colors):
            color_index = 0'''

    # Get comparison files, 
    # These are files common to all models

    basenames = []
    
    for file in os.listdir(input_dir):
        if file.endswith(".plotly"):
            basenames.append(''.join(file.split('__')[1:]))

    basenames = list(set(basenames))
    files_tocompare = []

    for basename in basenames:
        to_compare = True
        
        for data_raw in dataset_raw:
            fpth = os.path.join(input_dir,"{0}__{1}".format(data_raw[0],basename))
            if not os.path.exists(fpth):
                to_compare = False
                
        if to_compare:
            files_tocompare.append(basename)

    with open("test.txt", "w") as text_file:
        print("{0}".format(dataset_raw), file=text_file)

    # Create Comparison Graph, for each file
    for filename in files_tocompare:
        data_out = []
        legend_names = []
        for data_raw in dataset_raw:
            fpth = os.path.join(input_dir,"{0}__{1}".format(data_raw[0],filename))
            graph = pio.read_json(fpth)['data']
            for scatter in graph:
                if scatter['name'] not in legend_names:
                    plot = scatter
                    plot['line']['width'] = 1.5
                    if scatter['name'] != "External temperature":
                        if data_raw[1]:
                            name = "{0} - {1} ({2})".format(scatter['name'], data_raw[1], os.path.basename(data_raw[0]))
                        else:
                            name = "{0} - {1}".format(scatter['name'], os.path.basename(data_raw[0]))
                        plot['name'] = name
                        plot['line']['color'] = data_raw[2]
                        
                        data_out.append(plot)
                    else:
                        plot['line']['color'] = exttemp_colour
                        data_out.insert(0, plot)

                    legend_names.append(plot['name'])

        fpth = os.path.join(input_dir,"{0}__{1}".format(dataset_raw[0][0],filename))
        layout = pio.read_json(fpth)['layout']
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
        fig.write_image(os.path.join(outputs['0'], os.path.splitext(filename)[0] + '.png'))
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


    main(calc_inputs,outputs, config['fdir_compareinputs'])
    print('done')

