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

    # Create Dataset
    exttemp_colour = "Crimson"
    benchmark_colour = "DodgerBlue"
    asdesigned_colour = "MediumSeaGreen"
    dataset_raw = []
    dataset_raw.append((inputs["Benchmark"],"Benchmark", benchmark_colour))
    dataset_raw.append((inputs["As Designed"],"As Designed", asdesigned_colour))
    colors = ["Peru",
            "LightGray",
            "Turquoise",
            "darksalmon",
            "goldenrod"]
    color_index = 0
    for i in inputs["Comparison"]:
        dataset_raw.append((i,"",colors[color_index]))
        color_index += 1
        if color_index > len(colors):
            color_index = 0

    # Get comparison files, 
    # These are common the files common to all models
    files_count = {}
    files_tocompare = []
    for data_raw in dataset_raw:
        for file in os.listdir(data_raw[0]):
            if file.endswith(".plotly"):
                if file in files_count:
                    files_count[file] += 1
                else:
                    files_count[file] = 1

    for file in files_count:
        if files_count[file] == len(dataset_raw):
            files_tocompare.append(file)


    # Create Comparison Graph, for each file
    for filename in files_tocompare:
        data_out = []
        legend_names = []
        for data_raw in dataset_raw:
            graph = pio.read_json(os.path.join(data_raw[0], filename))['data']
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

        layout = pio.read_json(os.path.join(dataset_raw[0][0], files_tocompare[0]))['layout']
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

