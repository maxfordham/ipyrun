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
import functools
import operator

try:
    from ipyword.ipyword import md_to_docx, md_to_pdf
except:
    from ipyword import md_to_docx, md_to_pdf

def find_imgs(fdir, prefix=None):
    imgs = []
    for filename in os.listdir(fdir):
        if prefix and filename.startswith(prefix):
            if filename.endswith('.png') or filename.endswith('.jpg') or filename.endswith('.jpeg'):
                fullname = os.path.join(fdir, filename)
                imgs.append(fullname)
    return imgs

def get_results(tagname, inputs):
    for _, process_value in inputs.items():
        if('comparison-graphs' in process_value[1]):
            return process_value[0]

def get_processes(tagname, inputs):
    output = []
    for _, process_value in inputs.items():
        if(tagname in process_value[1] and 'label' not in process_value[1]):
            [numtag] = [tag for tag in process_value[1] if tag.isdigit()] or [""]
            for _, name_value in inputs.items():
                if(numtag in name_value[1] and tagname in name_value[1] and 'label' in name_value[1]):
                    output.append((process_value[0],name_value[0]))
                    continue
    return output

def img_string(img, caption="", size=None):
    size = size if size else 500
    return '![{0}]({1}){{width={2}px}}'.format(caption, img, size)

def read_modelrun_inputs(basename, fpth_parameters):
    fpth = os.path.join(fpth_parameters['fdir_inputs'], '{0}.json'.format(basename[0]))
    inputs = read_json(fpth)
    calc_inputs = {}

    def parse_inputs(values, inputs, name):
        # Input parse for JSON file
        for l in values:
            if l['name'] != 'Linked Files' and l['name'] !='Refs' and l['name'] !='Model File Path' and l['name'] != 'Fabrics - Breakdown':
                if type(l['value']) is list:
                    inputs = parse_inputs(l['value'], inputs, l['name'])
                else:
                    inputs[l['name']] = [l['value']]
        return inputs

    calc_inputs = parse_inputs(inputs, calc_inputs, 'Misc')
    df = pd.DataFrame(data=calc_inputs)
    df = df.T
    df.columns = [basename[1]]
    return df

def main(inputs, outputs, fpth_parameters, analysis_name):

    # --------------------
    # Report
    # --------------------

    report = []

    tmp = []
    benchmark_process = get_processes('benchmark', inputs)
    if benchmark_process:
        for process in benchmark_process:
            imgs = find_imgs(fdir=fpth_parameters['fdir_analysis_interim'], prefix=process[0])
            if imgs:
                tmp.append(process[1])
                tmp += [img_string(img, "", 800) for img in imgs]
    if tmp:
        report.append('### Baseline Assessment')
        report += tmp
        report.append('<br>')

    tmp = []
    processes = get_processes('heatwave', inputs)
    if processes:
        for process in processes:
            imgs = find_imgs(fdir=fpth_parameters['fdir_analysis_interim'], prefix=process[0])
            if imgs:
                tmp.append(process[1])
                tmp += [img_string(img, "", 800) for img in imgs]
    if tmp:
        report.append('### Heatwave Assessment')
        report += tmp
        report.append('<br>')

    tmp = []
    processes = get_processes('future', inputs)
    if processes:
        for process in processes:
            imgs = find_imgs(fdir=fpth_parameters['fdir_analysis_interim'], prefix=process[0])
            if imgs:
                tmp.append(process[1])
                tmp += [img_string(img, "", 800) for img in imgs]
    if tmp:
        report.append('### Future Assessment')
        report += tmp

    if report:
        report.append(r'\newpage')

    tmp = []

    imgs = find_imgs(fdir=fpth_parameters['fdir_graphs_interim'], prefix=benchmark_process[0][0] + '__crit_category')
    tmp += [img_string(img, "", 1200) for img in imgs]

    if(analysis_name == 'TM59'):
        imgs = find_imgs(fdir=fpth_parameters['fdir_graphs_interim'], prefix=benchmark_process[0][0] + '__av_non_bedroom')
        tmp += [img_string(img, "", 1200) for img in imgs]

        imgs = find_imgs(fdir=fpth_parameters['fdir_graphs_interim'], prefix=benchmark_process[0][0] + '__av_bedroom')
        tmp += [img_string(img, "", 1200) for img in imgs]
    else:
        imgs = find_imgs(fdir=fpth_parameters['fdir_graphs_interim'], prefix=benchmark_process[0][0] + '__av_space')
        tmp += [img_string(img, "", 1200) for img in imgs]

    if tmp:
        report.append('### Results Breakdown: Proposed Design')
        report += tmp
        report.append(r'\newpage')

    imgs = []

    for value in get_results('comparison-graphs',inputs):
        imgs_tmp = find_imgs(fdir=fpth_parameters['fdir_graphs_interim'], prefix=benchmark_process[0][0] + '__' + value.split(".")[0])
        imgs += imgs_tmp

    if imgs:
        report.append('### Temperature Breakdown: Proposed Design')
        temp_img_strings = [img_string(img, "", 300) for img in imgs]
        if temp_img_strings:
            if len(temp_img_strings) > 1:
                df = pd.DataFrame([temp_img_strings[::2], temp_img_strings[1::2]]).T
                df.columns = ['Graphs of Example Rooms', '']
            else:
                df = pd.DataFrame([temp_img_strings]).T
                df.columns = ['Graphs of Example Rooms']
        report.append(df.to_markdown(showindex=False))
        report.append(r'\newpage')

    all_processes = get_processes('benchmark', inputs) + get_processes('heatwave', inputs) + get_processes('future', inputs)
    dfs = []
    for process in all_processes:
        if process[0]:
            dfs.append(read_modelrun_inputs(process, fpth_parameters))

    df = pd.concat(dfs, axis=1)
    report.append(df.to_markdown(showindex=True))

    report_name =  '{0}_Report'.format(analysis_name)

    md_path = os.path.join(outputs['1'], '{0}.md'.format(report_name))
    docx_path = os.path.join(outputs['0'], '{0}.docx'.format(report_name))
    pdf_path = os.path.join(outputs['0'], '{0}.pdf'.format(report_name))

    with open(md_path, 'w', encoding="utf-8") as f:
        for m in report:
            f.write("%s\n\n" % m)

    #md_to_docx(fpth_md=md_path, fpth_docx=docx_path)
    md_to_pdf(fpth_md=md_path, fpth_pdf=pdf_path)

    return

script_outputs = [
    {
        'fdir':'',
        'fnm': r'',
        'description': "Reports Directory"
    },
    {
        'fdir':'',
        'fnm': r'',
        'description': "Markdown Directory"
    }
]

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

    calc_inputs = get_inputs(inputs, {})

    main(calc_inputs, outputs, config['fpth_parameters'], config['analysis_name'])
    print('done')

