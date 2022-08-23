import json
import pandas as pd
import numpy as np
from types import SimpleNamespace
from app.support import *

# Identify data input
class clean_input:
    def __init__(self, load_data):
        self.load_data = load_data

    def profile(self):
        if self.load_data.load_type == 'NOMIAL':
            self.load_sel = self.load_data.load_selection.lower()
            self.nominal_load = self.load_data.load_value
            self.load_profile = 0
        else:
            self.load_sel = 0
            self.nominal_load = 0
            self.load_profile = self.load_data.load_profiles
        return self

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
        
        # Study the load profile and flatten for CTES
        if self.nominal_load != 0:
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
        
        # Tariff Profile
        tariff_profile = tariffcalc(country_data, p_profile).tariffprofile()
        all_profiles = costingprof(tariff_profile, chiller_profiles).costprof()

        # Get total daily cost of setup
        chiller_capex = chiller_cost_factor*oversized_chiller
        chiller_lcoc = lcoc(all_profiles).cooling()

        # Clean data
        clean_profiles = cleandata(lowest_chiller_models, all_profiles).clear()

        res = {'chiller_profiles': clean_profiles,
                'chiller_models': models,
                'chiller_CAPEX': round(chiller_capex, 2),
                'chiller_LCOC': round(chiller_lcoc, 2),
                'currency': currency,
                'p_profile' : p_profile
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

# # CTES integration
# class ctes_setup:
#     def __init__(self, finance, results):
#         self.finance = finance
#         self.results = results

#     def info(self):
#         ctes_lcos = self.finance.lcos
#         ctes_capex = self.finance.capex
#         p_profile = self.results.p_profile
#         chiller_lcoc = self.results.chiller_LCOC
#         chiller_capex = self.results.chiller_CAPEX                                                                                            

#         self.totalcost = ctes_lcos + ctes_capex + chiller_lcoc + chiller_capex
#         self.newprofile = p_profile