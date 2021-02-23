# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.4.2
#   kernelspec:
#     display_name: Python [conda env:mf_main] *
#     language: python
#     name: conda-env-mf_main-py
# ---

import os
import importlib.util
from shutil import copyfile
from mf_modules.datamine_functions import recursive_glob
from mf_modules.file_operations import make_dir
from mf_modules.pydtype_operations import write_json    
import copy
FDIR = os.path.dirname(os.path.realpath('__file__'))

from pydantic import BaseModel, FilePath
import pathlib

pathlib.PureWindowsPath()

# +
from dataclasses import dataclass, field, asdict

@dataclass
class Config:
    
    jobno: int
    fpth_script: str
    #script_outputs_template: str
    process_name: str
    pretty_name: str
    fdir_appdata: str
    fdir_inputs: str
    fdir_inputs_archive: str
    fdir_template_inputs: str
    #fpth_template_input: str
    #fdir: pathlib.Path = '.'

from_dict(data=rc.config,data_class=Config)
# -

rc.config



# ?FilePath

type(pathlib.Path(di['fpth_script'])) == type(pathlib.Path())

li = list(Config.__dict__['__annotations__'].keys())
li

di = {l:rc.config[l] for l in li if l in rc.config.keys()}

di

from dacite import from_dict

# from dataclasses import dataclass, field, asdict
# @dataclass
# class Config:
#     fdir: str
#     jobno: int
#     fpth_script: FilePath
#     script_outputs_template: pathlib.Path
#     process_name: str
#     pretty_name: str
#     fdir_appdata: pathlib.Path
#     fdir_inputs: pathlib.Path
#     fdir_inputs_archive: pathlib.Path
#     fdir_template_inputs: pathlib.Path
#     fpth_template_input: pathlib.Path
#     template_input_ext 
#     fpth_inputs
#     fpth_inputs_options #dict
#     script_outputs#dict
#     fnms_outputs #list
#     fpths_outputs #list
#     fdir_log 
#     fnm_log 
#     fpth_log 
#     fdir_config 
#     fnm_config
#     fpth_config 
#     fdir_outputs

# +


class RunConfig():

    def __init__(self,config,lkup_script=True):
        """
        class that creates a default configuration of filepaths for:
            - script filepath
            - data outputs directories and filename
            - log file directory and filename
            - script input file (passed as argument to script) filepath
            - a list of template or user modified script input files
                (the user can then choose from templates or previous versions)
        for simplicity and standardisation, it is strongly suggested that the defaults
        defined by this class are used. This allows the developer to pass minimal information
        and receive an out-of-the-box configuration. That said, if more information is passed
        in the config dict the user-defined inputs will always be favoured allowing for custom
        configurations. The required folders are created when the script runs.

        Args:
            config (di): a user configuration dict defining the script location and file
                locations of outputs and log file

        Example:
            ```
            config={
                'fpth_script':os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),
                'fdir':'.',
                }
            m = RunConfig(config)
            from pprint import pprint
            >>> pprint(m.config)
            {'fdir': '.',
             'fdir_config': '.\\appdata\\config',
             'fdir_inputs': '.\\appdata\\inputs',
             'fdir_log': '.\\appdata\\log',
             'fnm_config': 'config-eplus_pipework_params.json',
             'fnm_log': 'log-eplus_pipework_params.csv',
             'fpth_config': '.\\appdata\\config\\config-eplus_pipework_params.json',
             'fpth_inputs': '.\\appdata\\inputs\\eplus_pipework_params.csv',
             'fpth_inputs_options': {'project': {'fdir': '.\\appdata\\inputs',
                                                 'fpths': ['.\\appdata\\inputs\\eplus_pipework_params.csv']},
                                     'template': {'fdir': 'C:\\engDev\\git_mf\\MF_Toolbox\\dev\\mf_scripts\\template_inputs',
                                                  'fpths': ['C:\\engDev\\git_mf\\MF_Toolbox\\dev\\mf_scripts\\template_inputs\\eplus_pipework_params.csv']}},
             'fpth_log': '.\\appdata\\log\\log-eplus_pipework_params.csv',
             'fpth_script': 'C:\\engDev\\git_mf\\MF_Toolbox\\dev\\mf_scripts\\eplus_pipework_params.py',
             'script_outputs': {'0': {'description': 'a csv lookup table with the backend '
                                                    'nomenclature of how pipework '
                                                    'characteristics are named within '
                                                    'energyPlus.',
                                     'fdir': '..\\data\\external',
                                     'fnm': 'eplus_pipework_params.csv'}},
             'pretty_name': 'eplus_pipework_params',
             'process_name': 'eplus_pipework_params'}
             ```
        """
        self._init_RunConfig(config,lkup_script=lkup_script)
        
    def _init_RunConfig(self,config,lkup_script=True):
        self.config = config
        self.lkup_script = lkup_script
        self.user_keys = list(config.keys())
        self.errors = []
        self._update_config()
        self.make_dirs()
    
    def _update_config(self):
        """
        a configuration dict is passed to the app that defines the configuration variables
        of the app. e.g filepaths for the script path, user inputs template file etc.
        where explicit inputs are not given this function updates the config dict with
        default values, flagging any errors that are spotted on the way.
        """

        # assign vars
        self.fdir = os.path.realpath(self._check_or_make_var('fdir',default='.'))
        self.jobno = self._jobno()
        self.fpth_script = self.config['fpth_script']
        self.script_name = os.path.splitext(os.path.split(self.config['fpth_script'])[1])[0]
        self.script_outputs_template = self._script_outputs_template()
        self.process_name = self._check_or_make_var('process_name',default=self.script_name)
        self.pretty_name = self._check_or_make_var('pretty_name',default=self.process_name)
        self.fdir_appdata = self._check_or_make_var('fdir_appdata',default=os.path.join(self.fdir,r'appdata')) 
        self.fdir_inputs = self._check_or_make_var('fdir_inputs',default=os.path.join(self.fdir,self.fdir_appdata,'inputs')) 
        self.fdir_inputs_archive = self._check_or_make_var('fdir_inputs_archive',default=os.path.join(self.fdir,self.fdir_appdata,'archive')) 
        self.fdir_template_inputs = self._check_or_make_var('fdir_inputs_archive',default=os.path.join(os.path.dirname(self.config['fpth_script']),r'template_inputs')) 
        self.fpth_template_input = self._fpth_template_input()
        self.template_input_ext = self._template_input_ext()
        self.fpth_inputs = self._fpth_inputs()
        self.fpth_inputs_options = self._fpth_inputs_options() #dict
        self.script_outputs = self._update_script_outputs() #dict
        self.fnms_outputs, self.fpths_outputs = self._fpths_outputs()
        self.fdir_log = self._check_or_make_var('fdir_log',default=os.path.join(self.fdir_appdata,'log'))
        self.fnm_log = self._check_or_make_var('fdir_log',default='log-' + self.process_name + '.csv')
        self.fpth_log = os.path.join(self.fdir_log, self.fnm_log)
        self.fdir_config = self._check_or_make_var('fdir_config',default=os.path.join(self.fdir_appdata,'config'))
        self.fnm_config = self._check_or_make_var('fdir_config',default='config-' + self.process_name + '.json') ## self._fnm_config()
        self.fpth_config = os.path.join(self.fdir_config, self.fnm_config)
        self.fdir_outputs = self._fdir_outputs()

        # update config
        self.config['fdir'] = self.fdir
        self.config['jobno'] = self.jobno
        self.config['process_name'] = self.process_name
        self.config['pretty_name'] = self.pretty_name
        self.config['fdir_appdata'] = self.fdir_appdata
        self.config['fdir_inputs'] = self.fdir_inputs
        self.config['fdir_inputs_archive'] = self.fdir_inputs_archive
        self.config['fdir_template_inputs'] = self.fdir_template_inputs 
        self.config['fpth_inputs'] = self.fpth_inputs
        self.config['fpth_inputs_options'] = self.fpth_inputs_options #dict
        self.config['script_outputs'] = self.script_outputs #dict
        self.config['fpths_outputs'] = self.fpths_outputs
        self.config['fdir_log'] = self.fdir_log
        self.config['fnm_log'] = self.fnm_log
        self.config['fpth_log'] = self.fpth_log
        self.config['fdir_config'] = self.fdir_config
        self.config['fnm_config'] = self.fnm_config
        self.config['fpth_config'] = self.fpth_config
        self.config['fdir_outputs'] = self.fdir_outputs  

    def make_dirs(self):
        for k,v in self.config.items():
            if 'fdir' in k:
                try:
                    make_dir(v)
                except:
                    pass
        
    def _check_or_make_var(self,varname,default=None):
        if varname in self.user_keys:
            return self.config[varname]
        else:
            return default

    def _fdir_outputs(self):
        try:
            return [os.path.realpath(v['fdir']) for k, v in self.script_outputs.items()]
        except:
            pass

    def _jobno(self):
        """check if fdir given, otherwise put it local to app"""
        if self.fdir == '.':
            return 'engDev'
        else:
            path = os.path.normpath(self.fdir)
            try:
                job_no = int(path.split(os.sep)[1][1:])
            except:
                job_no = 9999
            return job_no

    def _fpth_template_input(self):
        fpth = recursive_glob(rootdir=self.fdir_template_inputs,
                              pattern='*'+'inputs-' + self.script_name+'.*',
                              recursive=True)
        if len(fpth)==0:
            tmp = 'could not find template input: {0}'.format(os.path.join(self.fdir_inputs, self.process_name))
            self.errors.append(tmp)
            fpth.append(tmp)
        return fpth[0]

    def _template_input_ext(self):
        return os.path.splitext(self.fpth_template_input)[1]

    def _fpth_inputs(self):
        src = self.fpth_template_input
        ext = os.path.splitext(src)[1]
        if 'fpth_inputs' in self.user_keys:
            dstn = self.config['fpth_inputs']
        elif self.process_name is not self.script_name:
            dstn = os.path.join(self.fdir_inputs, 'inputs-'+self.process_name+ext)
        else:
            dstn = os.path.join(self.fdir_inputs, os.path.basename(src))

        if not os.path.isfile(dstn) and os.path.isfile(src):
            copyfile(src, dstn)
        return dstn

    def _fpth_inputs_options(self):
        patterns = ['*' + self.process_name + '*', '*' + self.script_name + '*']
        patterns = list(set(patterns))

        di = {
            'template':{
                'fdir': self.fdir_template_inputs,
                'fpths':[]
            },
            'project':{
                'fdir': self.fdir_inputs,
                'fpths':[]
            },
        }
        # NOTE. this is no longer how it gets the project files...
        # these are taken from the log.csv ouptut.

        cnt = 0
        valid_exts = ['.csv','.json']
        for k,v in di.items():
            for pattern in patterns:
                fpths = recursive_glob(rootdir=v['fdir'],pattern=pattern,recursive=True)
                fpths = [fpth for fpth in fpths if '.ipynb_checkpoints' not in fpth]
                di[k]['fpths'].extend(fpths)
                di[k]['fpths'] = list(set(di[k]['fpths']))
                cnt += len(fpths)
                self.errors.append(['{0} not csv or json'.format(fpth) for fpth in fpths if os.path.splitext(fpth)[1] not in valid_exts])
        if cnt == 0:
            self.errors.append('couldnt find and input files within the templates folder or in the project folder')
        return di

    def _script_outputs_template(self):
        """
        looks in the script file and finds and returns object called "script_outputs"
        """
        if self.lkup_script:
            if os.path.isfile(self.fpth_script):
                try:
                    spec = importlib.util.spec_from_file_location(self.script_name, self.fpth_script)
                    foo = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(foo)
                    script_outputs = foo.script_outputs
                except:
                    print('error loading script: {0}'.format(self.fpth_script)) #  add to logging instead
                    script_outputs = {}
            else:
                print('script not exist: {0}'.format(self.fpth_script)) #  add to logging instead
                script_outputs = {}
        else:
            print('user says skip: {0}'.format(self.fpth_script)) #  add to logging instead
            script_outputs = {}
        return script_outputs

    def _update_script_outputs(self):
        """overwrites the template fpth outputs with the user defined ones"""
        if 'script_outputs' not in self.user_keys:
            return self.script_outputs_template
        else:
            di = {}
            for k, v in self.script_outputs_template.items():
                di[k] = v
                for _k,_v in v.items():
                    di[k][_k] = self.config['script_outputs'][k][_k]
            return di

    def _fpths_outputs(self):
        fnms = {}
        fpths = {}
        for k, v in self.script_outputs.items():
            try:
                fnms.update({k:v['fnm']})
                fpths.update({k:os.path.realpath(os.path.join(v['fdir'],v['fnm']))})
            except:
                pass
        return fnms, fpths

    def config_to_json(self):
        write_json(self.config,
                   sort_keys=True,
                   indent=4,
                   fpth=self.config['fpth_config'],
                   print_fpth=False,
                   openFile=False)





# +
#  THIS CONFIG SETUP SHOULD BE BROKEN IN MULTIPLE SMALLER CLASSES THAT ARE COMBINED TO CREATE THE ONE BELOW. 
#  THIS WOULD ALLOW FOR, SAY, THE GENERATION OF THE INPUTS FILEPATHS WITHOUT THINKING ABOUT THE SCRIPT, ETC... 

if __name__ =='__main__':
    config = {
        'fpth_script':r'C:\engDev\git_mf\ipypdt\ipypdt\rvttxt_to_schedule.py',#os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),
        'process_name':'pipework',
        'fdir':'.',
        #'fpth_inputs':r'C:\engDev\git_mf\ipyrun\ipyrun\appdata\inputs\test\test.csv',
        #'fdir_inputs':r'C:\engDev\git_mf\ipyrun\ipyrun\appdata\inputs\test'
        }
    
    config = {
        'fpth_script':os.path.join(os.environ['MF_ROOT'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),#,
        'process_name':'pipework',
        'fdir':'.',
        #'fpth_inputs':r'C:\engDev\git_mf\ipyrun\ipyrun\appdata\inputs\test\test.csv',
        #'fdir_inputs':r'C:\engDev\git_mf\ipyrun\ipyrun\appdata\inputs\test'
        }
    from pprint import pprint
    rc = RunConfig(config,lkup_script=True)
    pprint(rc.config)




# -



