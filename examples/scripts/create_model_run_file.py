"""
Creates Model Run File

    Args:
        ** Set of Model Run Inputs

    Returns:
        ** Filepath, where data has been written to

    References:
        -   N/A

"""

import os
import pandas as pd
import numpy as np

dfDummy = pd.DataFrame(np.random.randint(0,100,size=(15, 4)), columns=list('ABCD'))

'''
def create_model_run():
    df1.to_excel("output.xlsx")  
    return dfDummy
'''

def main(inputs, outputs):
    df = pd.DataFrame(data=inputs)
    df.to_excel(outputs['0'])  
    return

script_outputs = {
    '0': {
        'fdir':'.', # relative to the location of the App / Notebook file
        'fnm': r'create_model_run.xlsx',
        'description': "Creates model run file."
    }
}

if __name__ == '__main__':

    print('test')
    import sys
    import os
    fpth_config = sys.argv[1]
    fpth_inputs = sys.argv[2]
    print('fpth_script: {0}'.format(sys.argv[0]))
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
    calc_inputs = []
    print(inputs)
    [calc_inputs.append([l['name'],l['value']]) for l in inputs]
    main(calc_inputs,outputs)
    print('done')
