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
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# +
import os
import importlib.util
from shutil import copyfile
from mf_modules.datamine_functions import recursive_glob
from mf_modules.file_operations import make_dir
from mf_modules.pydtype_operations import write_json    
FDIR = os.path.dirname(os.path.realpath('__file__'))

class RunConfig():

    def __init__(self,config):
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
                'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),
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
        self.config = config.copy()
        self.user_keys = list(config.keys())
        self.errors = []
        self._update_config()

    def _update_config(self):
        """
        a configuration dict is passed to the app that defines the configuration variables
        of the app. e.g filepaths for the script path, user inputs template file etc.
        where explicit inputs are not given this function updates the config dict with
        default values, flagging any errors that are spotted on the way.
        """

        # assign vars
        self.fdir = self._fdir()
        self.jobno = self._jobno()
        self.fpth_script = self.config['fpth_script']
        self.script_outputs_template = self._script_outputs_template()
        self.process_name = self._process_name()
        self.pretty_name = self._pretty_name()
        self.fdir_inputs = self._fdir_inputs()
        self.fdir_inputs_archive = self._fdir_inputs_archive()
        self.fdir_template_inputs = self._fdir_template_inputs()
        self.fpth_template_input = self._fpth_template_input()
        self.template_input_ext = self._template_input_ext()
        self.fpth_inputs = self._fpth_inputs()
        self.fpth_inputs_options = self._fpth_inputs_options() #dict
        self.script_outputs = self._update_script_outputs() #dict
        self.fnms_outputs, self.fpths_outputs = self._fpths_outputs()
        self.fdir_log = self._fdir_log()
        self.fnm_log = self._fnm_log()
        self.fpth_log = os.path.join(self.fdir_log, self.fnm_log)
        self.fdir_config = self._fdir_config()
        self.fnm_config = self._fnm_config()
        self.fpth_config = os.path.join(self.fdir_config, self.fnm_config)
        self.fdir_outputs = self._fdir_outputs()

        # update config
        self.config['fdir'] = self.fdir
        self.config['jobno'] = self.jobno
        self.config['process_name'] = self.process_name
        self.config['pretty_name'] = self.pretty_name
        self.config['fdir_inputs'] = self.fdir_inputs
        self.config['fdir_inputs_archive'] = self.fdir_inputs_archive
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

    def _fdir(self):
        """check if fdir given, otherwise put it local to app"""
        if 'fdir' in self.user_keys:
            return os.path.realpath(self.config['fdir'])
        else:
            return os.path.realpath('.')

    def _fdir_outputs(self):
        return [os.path.realpath(v['fdir']) for k, v in self.script_outputs.items()]

    def _jobno(self):
        """check if fdir given, otherwise put it local to app"""
        if self.fdir == '.':
            return 'engDev'
        else:
            string = self.fdir
            job_no=string[:4]
            return job_no

    @property
    def script_name(self):
        """name of the script. used for checking if its different to the process name"""
        return os.path.splitext(os.path.split(self.config['fpth_script'])[1])[0]

    def _process_name(self):
        """add process name. defaults to name of the script with optional overide.
        the names of the inputs files and log file always match the process_name"""
        process_name = self.script_name
        if 'process_name' in self.user_keys:
            return self.config['process_name']
        else:
            return process_name

    def _pretty_name(self):
        """pretty name. opportunity to add user-friendly name."""
        if 'pretty_name' in self.user_keys:
            return self.config['pretty_name']
        else:
            return self.process_name

    def _fdir_inputs(self):
        # add inputs folder name
        if 'fdir_inputs' in self.user_keys:
            make_dir(self.config['fdir_inputs'])
            return self.config['fdir_inputs']
        else:
            make_dir(os.path.join(self.fdir,r'appdata\inputs'))
            return os.path.join(self.fdir,r'appdata\inputs')

    def _fdir_inputs_archive(self):
        # add inputs folder name
        if 'fdir_inputs_archive' in self.user_keys:
            make_dir(self.config['fdir_inputs_archive'])
            return self.config['fdir_inputs_archive']
        else:
            make_dir(os.path.join(self.fdir,r'appdata\inputs\archive'))
            return os.path.join(self.fdir,r'appdata\inputs\archive')

    def _fdir_template_inputs(self):
        return os.path.join(os.path.dirname(self.config['fpth_script']),r'template_inputs')

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
        
        if 'fpth_inputs' in self.user_keys:
            dstn = self.config['fpth_inputs']
        else:
            dstn = os.path.join(self.fdir_inputs, os.path.basename(src))

        if not os.path.isfile(dstn):
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
                di[k]['fpths'] = fpths
                cnt += len(fpths)
                self.errors.append(['{0} not csv or json'.format(fpth) for fpth in fpths if os.path.splitext(fpth)[1] not in valid_exts])
        if cnt == 0:
            self.errors.append('couldnt find and input files within the templates folder or in the project folder')
        return di

    def _fdir_log(self):
        if 'fdir_log' in self.user_keys:
            return self.config['fdir_log']
        else:
            return os.path.join(self.fdir,r'appdata\log')

    def _fnm_log(self):
        if 'fnm_log' in self.user_keys:
            return self.config['fnm_log']
        else:
            return 'log-' + self.process_name + '.csv'

    def _fdir_config(self):
        if 'fdir_config' in self.user_keys:
            fdir = self.config['fdir_config']
            make_dir(fdir)
            return fdir
        else:
            fdir = os.path.join(self.fdir,r'appdata\config')
            make_dir(fdir)
            return fdir

    def _fnm_config(self):
        if 'fnm_config' in self.user_keys:
            return self.config['fnm_config']
        else:
            return 'config-' + self.process_name + '.json'

    def _script_outputs_template(self):
        """
        looks in the script file and finds and returns object called "script_outputs"
        """
        if os.path.isfile(self.fpth_script):
            spec = importlib.util.spec_from_file_location(self.script_name, self.fpth_script)
            foo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(foo)
            try:
                script_outputs = foo.script_outputs
            except:
                script_outputs = {'0' : 'no script outputs found in {0}'.format(self.fpth_script)}
        else:
            script_outputs = {'0' : '{0} script does not exist'.format(self.fpth_script)}
        return script_outputs

    def _update_script_outputs(self):
        """overwrites the template fpth outputs with the user defined ones"""
        if 'script_outputs' not in self.user_keys:
            return self.script_outputs_template
        else:
            di = {}
            for k, v in self.script_outputs_template.items():
                di[k] = v
                print(v)
                for _k,_v in v.items():
                    di[k][_k] = self.config['script_outputs'][k][_k]
            return di

    def _fpths_outputs(self):
        fnms = {}
        fpths = {}
        for k, v in self.script_outputs.items():
            fnms.update({k:v['fnm']})
            fpths.update({k:os.path.realpath(os.path.join(v['fdir'],v['fnm']))})
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
        'fpth_script':os.path.join(os.environ['mf_root'],r'MF_Toolbox\dev\mf_scripts\eplus_pipework_params.py'),
        'fdir':'.',
        #'fpth_inputs':r'C:\engDev\git_mf\ipyrun\ipyrun\appdata\inputs\test\test.csv',
        #'fdir_inputs':r'C:\engDev\git_mf\ipyrun\ipyrun\appdata\inputs\test'
        }
    from pprint import pprint
    rc = RunConfig(config)
    pprint(rc.config)


# -





