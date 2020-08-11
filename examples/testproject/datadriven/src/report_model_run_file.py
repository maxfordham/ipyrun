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

def main(inputs, outputs, fpth_parameters):

    # --------------------
    # Preamble
    # --------------------
    basenames = {}
    basenames['Benchmark'] = inputs['Benchmark']
    basenames['As Designed'] = inputs['As Designed']
    dfs = {}

    def read_modelrun_inputs(basename):
        fpth = os.path.join(fpth_parameters['fdir_inputs'], '{0}.json'.format(basename))
        inputs = read_json(fpth)
        calc_inputs = {}

        def get_inputs(values, inputs, name):
            for l in values:
                if type(l['value']) is list:
                    inputs = get_inputs(l['value'], inputs, l['name'])
                else:
                    if name != 'Linked Files':
                        inputs[l['name']] = [l['value'], l['label'], name]
            return inputs

        calc_inputs = get_inputs(inputs, calc_inputs, 'Misc')
        df = pd.DataFrame(data=calc_inputs)
        df = df.T
        df.columns = ['Parameter Values', 'Notes', 'Category']
        return df

    for name in basenames:
        dfs[name] = read_modelrun_inputs(basenames[name])

    # --------------------
    # Report
    # --------------------

    report = []

    
    report.append('## Analysis Details')
    report.append('This section outlines the details of the overheating analysis')

    analysisdesc = [
        '##### Software',
        '{0}'.format(inputs['Software']),
        '##### Site Location',
        '{0}'.format(inputs['Site Location']),
        '##### Site Image',
        '![]({0})'.format(r'../references/img/site_img.png'),
        '##### IES Modelling Image',
        '![]({0})'.format(r'../references/img/ies_img.png'),

    ]
        
    report += analysisdesc
    report.append('\\newpage')

    report.append('## TM59 Results')
    report.append('This section outlines the results from CIBSE TM59 analysis.')
    report.append('The CIBSE TM59 standard outlines a methodology for the assessment of overheating risk in homes. Two criteria are defined within this standard:\n* Criterion a: For living rooms, kitchens and bedrooms: the number of hours during which DT is greater than or equal to one degree (K) during the period May to September inclusive shall not be more than 3% of occupied hours.\n* Criterion b: For bedrooms only: the operative temperature from 10 pm to 7 am shall not exceed 26C for more than 1% of annual hours (33 hours)')
    report.append('In order to pass TM59, bedrooms have to pass both criteria while living rooms have to pass just Criterion a.')

    for name in basenames:
        report.append('### {0}'.format(name))
        fpth = os.path.join(fpth_parameters['fdir_tm59_interim'],'{0}__TM59results.jpeg'.format(basenames[name]))
        report.append('![]({0})'.format(fpth))

    report.append('\\newpage')
    report.append('## Individual Model Details')
    report.append('This section outlines the assumptions and design inputs used within the overheating modelling, for both the *Benchmark* and *As Designed* models')
    for name in basenames:
        
        report.append('### {0}'.format(name))
        
        df = dfs[name]
        modeldesc = [
            '##### Description',
            '{0}'.format(df.loc['Model Desc', 'Parameter Values']),
            '##### Fabric',
            'The parameters of the building fabric are detailed in the following table:',
            df.loc[df['Category'] == 'Fabrics', df.columns != 'Category'].to_markdown(),
            '##### Ventilation Description',
            '{0}'.format(df.loc['Vent Desc', 'Parameter Values']),
            '##### Cooling Description',
            '{0}'.format(df.loc['Cooling Desc', 'Parameter Values']),
            '##### Summer (Elevated) Air Speed',
            '{0} m/s'.format(df.loc['Air Speed', 'Parameter Values']),
        ]
        
        report += modeldesc

    report.append('\\newpage')
    report.append('## Indoor Temperature Graphs')
    report.append('This section compares the indoor temperatures for both the *Benchmark* and *As Designed* models, for a typical summer week.')
    report.append('A number of example rooms were used, to show an overview of the indoor temperatures across the building.')
    for filename in inputs['Comparison Graphs']:
        report.append('![]({0})'.format(filename))

    report.append('\\newpage')
    report.append('## Appendix A: Full Model Details')
    report.append('This section outlines all model inputs, for both the *Benchmark* and *As Designed* models')

    appendix_dfs = [df.rename(columns = {'Parameter Values': '{0} Value'.format(name)}) for name, df in dfs.items()]
    appendix_df = pd.concat(appendix_dfs, axis=1, join='inner', ignore_index=False, sort=False)
    appendix_df = appendix_df.loc[:,~appendix_df.columns.duplicated()]
    cols = [col for col in appendix_df if col not in ['Notes', 'Category']] + ['Notes', 'Category']
    appendix_df = appendix_df[cols]

    report.append(appendix_df.to_markdown())

    if not os.path.exists(os.path.dirname(outputs['0'])):
        os.makedirs(os.path.dirname(outputs['0']))

    with open(os.path.join(outputs['0'], 'overheating-report.md'), 'w', encoding="utf-8") as f:
        for m in report:
            f.write("%s\n\n" % m)

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

    calc_inputs = {}
    [calc_inputs.update({l['name']:l['value']}) for l in inputs]

    compare_run_inputs = read_json(config['compare_run_inputs'])
    [calc_inputs.update({l['name']:l['value']}) for l in compare_run_inputs]

    
    main(calc_inputs, outputs, config['fpth_parameters'])
    print('done')

