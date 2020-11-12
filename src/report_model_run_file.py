"""
A script that takes creates a report of the overheating analysis,
comparing both the 'As Designed' and 'Benchmark' options.
        
    Args:
        ** software: Software used for overheating analysis
        ** site_location: Location of the site
        ** image_of_the_site_plan: Image of the site, used as a figure in the report

    Returns:
        **  overheating_report: The final report, outputted as a PDF and Word document
        
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
from mf_modules.md_helpers import write_md
import datetime as dt
try:
    from ipyword.ipyword import md_to_docx, md_to_pdf
except:
    from ipyword import md_to_docx, md_to_pdf

def img_test(fdir, in_name, prefix=None):
    imgs = []
    name = None
    for filename in os.listdir(fdir):
        if prefix and filename.startswith(prefix):
            if filename.endswith('.png') or filename.endswith('.jpg') or filename.endswith('.jpeg'):
                fullname = os.path.join(fdir, filename)
                imgs.append(fullname)
                name = in_name

    return name, imgs

def get_results(tagname, inputs):
    processes = []
    names = []
    for key, value in inputs.items():
        if(tagname in value[1] and 'label' not in value[1]):
            processes.append(value[0])
            [numtag] = [tag for tag in value[1] if tag.isdigit()] or [""]
            for key, value in inputs.items():
                if(numtag in value[1] and tagname in value[1] and 'label' in value[1]):
                    names.append(value[0])
                continue
    return processes, names       

def img_string(img, caption="", size=None):
    size = size if size else 500
    return '![{0}]({1}){{width={2}px}}'.format(caption, img, size)

def main(inputs, outputs, fpth_parameters):

    # --------------------
    # Preamble
    # --------------------

    basenames = {}

    dfs = {}

    def read_modelrun_inputs(basename):
        fpth = os.path.join(fpth_parameters['fdir_inputs'], '{0}.json'.format(basename))
        inputs = read_json(fpth)
        calc_inputs = {}

        def get_inputs(values, inputs, name):
            for l in values:
                if type(l['value']) is list:
                    if l['name'] != 'Linked Files':
                        inputs = get_inputs(l['value'], inputs, l['name'])
                else:
                    inputs[l['name']] = [l['value'], l['label'], name]
            return inputs

        calc_inputs = get_inputs(inputs, calc_inputs, 'Misc')
        df = pd.DataFrame(data=calc_inputs)
        df = df.T
        df.columns = ['Parameter Values', '', 'Category']
        return df

    # --------------------
    # Report
    # --------------------

    report = []

    tmp = [] 
    benchmark_process, names = get_results('benchmark', inputs)
    if benchmark_process:
        for index, process in enumerate(benchmark_process):
            name, imgs = img_test(fdir=fpth_parameters['fdir_analysis_interim'], prefix=process, in_name=names[index])
            if name:
                tmp.append(name)
                tmp += [img_string(img, "", 800) for img in imgs]
    if tmp:
        report.append('### Baseline Assessment')
        report += tmp
        report.append('<br>')

    tmp = [] 
    processes, names = get_results('heatwave', inputs)
    if processes:
        for index, process in enumerate(processes):
            name, imgs = img_test(fdir=fpth_parameters['fdir_analysis_interim'], prefix=process, in_name=names[index])
            if name:
                tmp.append(name)
                tmp += [img_string(img, "", 800) for img in imgs]
    if tmp:
        report.append('### Heatwave Assessment')
        report += tmp
        report.append('<br>')

    tmp = [] 
    processes, names = get_results('future', inputs)
    if processes:
        for index, process in enumerate(processes):
            name, imgs = img_test(fdir=fpth_parameters['fdir_analysis_interim'], prefix=process, in_name=names[index])
            if name:
                tmp.append(name)
                tmp += [img_string(img, "", 800) for img in imgs]
    if tmp:
        report.append('### Future Assessment')
        report += tmp

    if report:
        report.append(r'\newpage')

    tmp = [] 

    _, imgs = img_test(fdir=fpth_parameters['fdir_graphs_interim'], prefix=benchmark_process[0] + '__crit_category', in_name="")
    tmp += [img_string(img, "", 1200) for img in imgs]

    _, imgs = img_test(fdir=fpth_parameters['fdir_graphs_interim'], prefix=benchmark_process[0] + '__av_non_bedroom', in_name="")
    tmp += [img_string(img, "", 1200) for img in imgs]

    _, imgs = img_test(fdir=fpth_parameters['fdir_graphs_interim'], prefix=benchmark_process[0] + '__av_bedroom', in_name="")
    tmp += [img_string(img, "", 1200) for img in imgs]

    if tmp:
        report.append('### Results Breakdown: Proposed Design')
        report += tmp
        report.append(r'\newpage')

    tmp = [] 
    imgs = []
    processes = []
    for key, value in inputs.items():
        if('comparison-graphs' in value[1]):
            for process in value[0]:
                _, imgs_tmp = img_test(fdir=fpth_parameters['fdir_graphs_interim'], prefix=benchmark_process[0] + '__' + process, in_name="")
                imgs += imgs_tmp
            continue

    tmp += [img_string(img, "", 500) for img in imgs]  
    if tmp:
        report.append('### Temperature Breakdown: Proposed Design')
        report += tmp
        report.append(r'\newpage')
        
    _, imgs = img_test(fdir=fpth_parameters['fdir_graphs_interim'], prefix=benchmark_process[0] + '__temps', in_name="")
    temp_img_strings = [img_string(img, "", 300) for img in imgs]
    if temp_img_strings:
        df = pd.DataFrame([temp_img_strings[::2], temp_img_strings[1::2]]).T
        df.columns = ['Graphs of Example Rooms', '']

        report.append(df.to_markdown(showindex=False))

    md_path = os.path.join(outputs['0'], 'overheating_report.md')

    with open(md_path, 'w', encoding="utf-8") as f:
        for m in report:
            f.write("%s\n\n" % m)
            
    for key, value in inputs.items():
        if('word-out' in value[1]):
            if value[0]:
                md_to_docx(fpth_md=md_path)
    
    #md_to_pdf(fpth_md=md_path)
    return

script_outputs = {
    '0': {
        'fdir':'', # relative to the location of the App / Notebook file
        'fnm': r'',
        'description': "Creates model run file."
    }
}

if __name__ == '__main__':

    fpth_config = sys.argv[1]
    fpth_inputs = sys.argv[2]

    config = read_json(fpth_config)
    os.chdir(config['fdir']) # change the working dir to the app that is executing the script
    outputs = config['fpths_outputs']

    for output in list(outputs.values()):
        if not os.path.exists(output):
            os.mkdir(output)

    inputs = read_json(fpth_inputs)

    def get_inputs(values, inputs):
        for l in values:
            if type(l['value']) is list and type(l['value'][0] if l['value'] else None) is dict:
                inputs = get_inputs(l['value'], inputs)
            else:
                if 'tags' in l:
                    inputs[l['name']] = [l['value'], l['tags']]
                else:
                    inputs[l['name']] = [l['value'], []]
                
        return inputs

    calc_inputs = {}
    calc_inputs = get_inputs(inputs, calc_inputs)

    main(calc_inputs, outputs, config['fpth_parameters'])
    print('done')

