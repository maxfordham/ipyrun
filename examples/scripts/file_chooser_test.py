"""
a simple calc for sizing expansion vessels.

this docstring becomes the user guide so add anything the user needs to know here.

Calculates sizes and/or pressure ratings for heating system, including the expansion vessel and pumps.

    Args:
        ** water_volume_m3 (float): 15, default example
        ** height_difference_m (float): height between the highest and lowest point in the system
        ** eV_acceptance_fraction (float): additional volume / expansion vessel volume)
        ** pipework_length_m (float): Heating system pipework length (m), (includes horizontal, vertical, flow and return)
        ** pipework_pressure_loss_pa_per_m (float): pressure loss factor of pipework
        ** pipework_pressure_loss_margin_fraction (float): error margin
        ** water_expansion_fraction (float): 0.03. 2.2% for 4-70°C. Have rounded up to 3% to be conservative.
            Based on water densities at different temperatures. This needs to be modified based on the temperature
            regime of the system.
        ** margin_1_bar (float): 0.3. BS7074...
        ** margin_2_bar (float): 0.15. Rule of Thumb from Paul Button

    Returns:
        df (pd.DataFrame): dataframe with inputs and outputs of expansion vessel calc, see example below
            |    | index                                                        | value              |
            |---:|:-------------------------------------------------------------|:-------------------|
            |  0 | Heating system water volume (m³)                             | 20.0               |
            |  1 | Change in height (m)                                         | 48                 |
            |  2 | Expansion vessel acceptance factor                           | 0.3                |
            |  3 | Heating system pipework length (m)                           | 257                |
            |  4 | Pipework pressure loss (Pa/m)                                | 500                |
            |  5 | Margin for pressure loss due to pipework fittings (fraction) | 1                  |
            |  6 | Cold fill pressure (bar-gauge)                               | 5.41512            |
            |  7 | Water expansion coefficient                                  | 0.03               |
            |  8 | Additional water volume (m³)                                 | 0.6                |
            |  9 | Expansion vessel volume (m³)                                 | 2.0                |
            | 10 | Expansion vessel minimum gas volume (m³)                     | 1.4                |
            | 11 | Expansion vessel maximum gas pressure (bar-absolute)         | 9.164457142857144  |
            | 12 | Expansion vessel maximum gas pressure (bar-gauge)            | 8.164457142857144  |
            | 13 | Heating system max. pressure (bar-gauge)                     | 10.734457142857144 |
            | 14 | Heating system pressure rating                               | PN16               |

    References:
        BS7074 - page?

Image:
    %mf_root%\engDevSetup\dev\icons\icon_png\expansion_vessel.jpg
"""

import os
import pandas as pd
# from mf_modules.xlsx_templater import to_excel, params_readme

def ev_sizing(water_volume_m3=15,
              height_difference_m=48,
              eV_acceptance_fraction=0.3,
              pipework_length_m=257,
              pipework_pressure_loss_pa_per_m=500,
              pipework_pressure_loss_margin_fraction=1,
              water_expansion_fraction=0.03,
              margin_1_bar=0.3,
              ):
    """
    Calculates sizes and/or pressure ratings for heating system, including the expansion vessel and pumps.

    Args:
        ** water_volume_m3 (float): 15, default example
        ** height_difference_m (float):
        ** eV_acceptance_fraction (float):
        ** pipework_length_m (float):
        ** pipework_pressure_loss_pa_per_m (float):
        ** pipework_pressure_loss_margin_fraction (float):
        ** water_expansion_fraction (float): = 0.03. 2.2% for 4-70°C. Have rounded up to 3% to be conservative.
            Based on water densities at different temperatures. This needs to be modified based on the temperature
            regime of the system.
        ** margin_1_bar (float): = 0.3. BS7074...
        ** margin_2_bar (float): = 0.15. Rule of Thumb from Paul Button

    Returns:
        df (pd.DataFrame): add description

    References:
        BS7074 - page?

    """
    # print("Calculation inputs:")
    # print(" ")
    # print("Heating system water volume (m³): ", water_volume_m3)
    # print("Change in height (m): ", height_difference_m)
    # print("Expansion vessel acceptance factor (= additional volume / expansion vessel volume): ", eV_acceptance_fraction)
    # print("Heating system pipework length (m): ", pipework_length_m,". Note: includes horizontal, vertical, flow and return.")
    # print("Pipework pressure loss (Pa/m): ", pipework_pressure_loss_pa_per_m)
    # print("Margin for pressure loss due to pipework fittings (fraction): ", pipework_pressure_loss_margin_fraction,) #E.g. 1 allows for pressure_loss*(1+1)
    # print(" ")

    # State 1:
    # Heating system is charged with cold water at around ~4°C.
    # The pressure has to be sufficient to push the water to the top of the system, plus some additional pressure to remove air bubbles.
    # This pressure is know as the Cold Fill Pressure.
    # The dry side of the expansion vessel is charged with air to the Cold Fill Pressure, so that there is no water within the expansion vessel.
    static_pressure_barg = 1000 * 9.81 * height_difference_m / 100000
    margin_2_bar = 0.15 * static_pressure_barg  # Rule of Thumb from Paul Button
    design_margin_1 = max(margin_1_bar, margin_2_bar)
    cold_fill_pressure_barg = static_pressure_barg + design_margin_1
    cold_fill_pressure_barabs = cold_fill_pressure_barg + 1

    # State 2:
    # The water within the heating system is heated from 4°C to 70°C, and expands into the expansion vessel.
    # The amount it expands by is the Additional Water Volume.
    # Typically the expansion vessel is sized to be ~3x the additional water volume.
    additional_water_volume = water_volume_m3 * water_expansion_fraction
    expansion_vessel_volume_m3 = additional_water_volume / eV_acceptance_fraction

    # As the water expands, the gas pressure within the expansion vessel increases.
    gas_volume_state_2_m3 = expansion_vessel_volume_m3 - additional_water_volume
    ev_gas_pressure_state_2_barabs = cold_fill_pressure_barabs * expansion_vessel_volume_m3 / gas_volume_state_2_m3
    ev_gas_pressure_state_2_barg = ev_gas_pressure_state_2_barabs - 1

    # Calculation of pump pressure rating
    # Need to check with Paul if this is correct - should this be gauage or absolute pressure?
    pump_pressure_barg = pipework_pressure_loss_pa_per_m * (
                1 + pipework_pressure_loss_margin_fraction) * pipework_length_m / 100000

    # Calculation of heating system pressure rating
    # Need to check with Paul if this is correct - should this be gauage or absolute pressure?
    heating_system_pressure_barg = pump_pressure_barg + ev_gas_pressure_state_2_barg
    x = heating_system_pressure_barg

    if x < 6:
        y = "PN6"
    elif x < 10:
        y = "PN10"
    elif x < 16:
        y = "PN16"
    elif x < 25:
        y = "PN25"
    else:
        y = ">PN25"
    heating_system_pressure_rating = y

    # create a df of results
    names = ['Heating system water volume (m³)', 'Change in height (m)', 'Expansion vessel acceptance factor',
             'Heating system pipework length (m)',
             'Pipework pressure loss (Pa/m)', 'Margin for pressure loss due to pipework fittings (fraction)',
             'Cold fill pressure (bar-gauge)',
             'Water expansion coefficient', 'Additional water volume (m³)', 'Expansion vessel volume (m³)',
             'Expansion vessel minimum gas volume (m³)',
             'Expansion vessel maximum gas pressure (bar-absolute)', 'Expansion vessel maximum gas pressure (bar-gauge)',
             'Heating system max. pressure (bar-gauge)',
             'Heating system pressure rating']
    values = [water_volume_m3, height_difference_m, eV_acceptance_fraction, pipework_length_m,
              pipework_pressure_loss_pa_per_m, pipework_pressure_loss_margin_fraction,
              cold_fill_pressure_barg, water_expansion_fraction, additional_water_volume, expansion_vessel_volume_m3,
              gas_volume_state_2_m3, ev_gas_pressure_state_2_barabs,
              ev_gas_pressure_state_2_barg, heating_system_pressure_barg, heating_system_pressure_rating]
    di = dict(zip(names, values))
    df = pd.DataFrame.from_dict(di,orient='index').rename(columns={0:'value'})
    return df.reset_index()

def main(inputs, outputs):

    #out = header.copy()
    #out['sheet_name'] = 'ev_sizing'
    #out['df'] = df
    ## out['xlsx_params'] = params_readme(df)
    #fpth = 'ev_sizing.xlsx'
    #to_excel(out, fpth, open=True)

    df = ev_sizing(**inputs)
    df.to_csv(outputs['0'])

    return df

script_outputs = {
    '0': {
        'fdir':'.', # relative to the location of the App / Notebook file
        'fnm': r'expansion_vessel_sizing.csv',
        'description': "a simple calc for sizing expansion vessels. could be expanded to size many vessels."
    }#,
    #'1': {
    #    'fdir': '.',  # relative to the location of the App / Notebook file
    #    'fnm': r'expansion_vessel_sizing.xlsx',
    #    'description': "a simple calc for sizing expansion vessels. could be expanded to size many vessels."
    #}
}

if __name__ == '__main__':

    if __debug__ == True:
        # you can hard-code some tests for fpth_config and fpth_inputs below.
        import sys
        import os
        fpth_config = r'C:\engDev\git_mf\ipyrun\examples\notebooks\appdata\config\config-expansion_vessel_sizing.json'#sys.argv[1]
        fpth_inputs = r'C:\engDev\git_mf\ipyrun\examples\notebooks\appdata\inputs\inputs-expansion_vessel_sizing.json'# sys.argv[2]
        print('fpth_script: {0}'.format(sys.argv[0]))
        print('fpth_config: {0}'.format(fpth_config))
        print('fpth_inputs: {0}'.format(fpth_inputs))
        from mf_modules.pydtype_operations import read_json
        from mf_modules.file_operations import make_dir

        # get config and input data
        # config
        config = read_json(fpth_config)
        os.chdir(config['fdir']) # change the working dir to the app that is executing the script
        outputs = config['fpths_outputs']
        [make_dir(fdir) for fdir in config['fdir_outputs']]
        # inputs
        inputs = read_json(fpth_inputs)

        # this is the only bit that will change between scripts
        calc_inputs = {}
        [calc_inputs.update({l['name']:l['value']}) for l in inputs];
        main(calc_inputs,outputs)
        print('done')


    else:
        # this is the bit that will be executed by the script
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
        config = read_json(fpth_config)
        os.chdir(config['fdir']) # change the working dir to the app that is executing the script
        outputs = config['fpths_outputs']
        [make_dir(fdir) for fdir in config['fdir_outputs']]
        # inputs
        inputs = read_json(fpth_inputs)

        # this is the only bit that will change between scripts
        calc_inputs = {}
        [calc_inputs.update({l['name']:l['value']}) for l in inputs];
        df = main(calc_inputs,outputs)
        print('done')
