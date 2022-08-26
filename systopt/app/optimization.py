import json
import pandas as pd
import numpy as np
from types import SimpleNamespace
from app.support import *

# Chiller Minimize 
class opt_mini:
    def __init__(self, country_sel, nominal_load, safety, load_sel, load_profile):
        self.country_sel = country_sel
        self.nominal_load = nominal_load
        self.safety = safety
        self.load_sel = load_sel
        self.load_profile = load_profile

    def minimize(self):
        # Import data 
        dataimp = dataimport(self.country_sel, self.load_sel).seldata()
        df_curves = dataimp['df_curves']
        country_data = dataimp['country_data']
        load_datal = dataimp['load_data']
        chiller_cost_factor = dataimp['chiller_cost_factor']
        
        # Currency selection
        currency = str(country_data['currency'].values[0])
        
        # Study the load profile
        if self.nominal_load != None:
            oversized_chiller = safechiller(self.safety, self.nominal_load).chiller_size()
            p_profile = (load_datal[load_datal.select_dtypes(include=['number']).columns]*oversized_chiller)
            
        else:
            temp = []
            temp2 = []
            if self.safety == 0:
                factor = 1
            else:
                factor = 1 + (self.safety/100)
            for x in self.load_profile:
                temp.append(x.value*factor)
                temp2.append(str(int(x.time*100)))
            temp = np.array(temp)
            oversized_chiller = np.max(temp)
            p_profile = pd.DataFrame(temp.reshape(-1, len(temp)), columns=[x for x in temp2])
        
        # Get the chiller models and profiles
        lowest_chiller_models = chillselect(df_curves, oversized_chiller).select()
        models = ' '.join(list(lowest_chiller_models))
        chiller_profiles = chillprof(df_curves, lowest_chiller_models, p_profile).prof()
        powercalc = chiller_profiles.loc[chiller_profiles['type'] == 'input_power']
        max_power = powercalc[powercalc.select_dtypes(include=['number']).columns].sum().max()
        
        # Tariff Profile
        tariff_profile = tariffcalc(country_data, p_profile).tariffprofile()
        all_profiles = costingprof(tariff_profile, chiller_profiles).costprof()

        # Get total daily cost of setup
        chiller_capex = chiller_cost_factor*oversized_chiller
        chiller_lcoc = lcoc(all_profiles).cooling()

        # Clean data
        clean_profiles = cleanprofiles(lowest_chiller_models, all_profiles).clear()

        res = {'chiller_profiles': clean_profiles,
                'chiller_models': models,
                'chiller_CAPEX': round(chiller_capex, 2),
                'chiller_LCOC': round(chiller_lcoc, 2),
                'currency': currency,
                'p_profile': p_profile,
                'max_power': max_power
                }

        results = SimpleNamespace(**res)
        return results

# Get CTES PQ
class ctes_values:
    def __init__(self, results):
        self.results = results

    def PQ(self):
        p_profile = self.results.p_profile

        q = areaUnder(p_profile.values[0]).curve()
        flatten_ctes_p_profile = np.array([q/len(p_profile.columns)]*len(p_profile.columns))
        flatten_ctes_p_profile = pd.DataFrame(flatten_ctes_p_profile.reshape(-1, len(flatten_ctes_p_profile)), columns=[x for x in p_profile.head()])
        ctes_discharge_hours = hoursctes(flatten_ctes_p_profile.values[0], p_profile.values[0]).ctesuse()
        self.ctes_q = chargeavail(flatten_ctes_p_profile.values[0], p_profile.values[0]).unusedchiller()
        self.ctes_p = (self.ctes_q/(ctes_discharge_hours))

        flatten_dict = flatten_ctes_p_profile.rename({0:'value'}, axis='index').transpose().reset_index(drop=True).rename_axis('time').reset_index().to_dict('records')
        self.flatten_ctes_p_profile = [SimpleNamespace(**x) for x in flatten_dict]

        return self

