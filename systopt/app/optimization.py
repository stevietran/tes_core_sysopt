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
        dataimp = dataimport(self.country_sel, self.load_sel).seldata() # Import data (Chiller curves, global data, sample load profile)
        df_curves = dataimp['df_curves']
        country_data = dataimp['country_data']
        load_datal = dataimp['load_data']
        chiller_cost_factor = dataimp['chiller_cost_factor']
        
        # Study the load profile
        if self.nominal_load != None:
            oversized_chiller = safechiller(self.safety, self.nominal_load).chiller_size() # Return oversized cooling load based on safety factor
            p_profile = (load_datal[load_datal.select_dtypes(include=['number']).columns]*oversized_chiller) # Return sample profile mutliplied by the oversized cooling load

        #  If user inputs a profile, this loop below multiplies each value of the profile with safety factor
        else:   # Also formats the data to fit in pandas hence the complication
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
        lowest_chiller_models = chillselect(df_curves, oversized_chiller).select() # Returns chiller models for the maximum cooling load
        models = ' '.join(list(lowest_chiller_models)) # Strings the output for backend
        chiller_profiles = chillprof(df_curves, lowest_chiller_models, p_profile).prof() # Returns the operation strategy for the chillers
        powercalc = chiller_profiles.loc[chiller_profiles['type'] == 'input_power'] # For calculating maximum electrical power used for the configuration (for pump power) 
        max_power = powercalc[powercalc.select_dtypes(include=['number']).columns].sum().max() # Calculates maximum electrical power used for the configuration (for pump power) 
        
        # Tariff Profile
        tariff_profile = tariffcalc(country_data, p_profile).tariffprofile() # Generates tariff profile based on the country selected (now only SG)
        all_profiles = costingprof(tariff_profile, chiller_profiles).costprof() # Generates the cost profile by multiplying electric profile with tariff profile

        # Get total daily cost of setup
        chiller_capex = chiller_cost_factor*oversized_chiller # Returns CAPEX
        chiller_lcoc = lcoc(all_profiles).cooling() # Returns LCOC

        # Clean data
        clean_profiles = cleanprofiles(lowest_chiller_models, all_profiles).clear() # Cleans all the profiles (load, electric, cost) for backend
        print(clean_profiles)

        res = {'chiller_profiles': clean_profiles,
                'chiller_models': models,
                'chiller_CAPEX': round(chiller_capex, 2),
                'chiller_LCOC': round(chiller_lcoc, 2),
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

        q = areaUnder(p_profile.values[0]).curve() # Returns area under the user profile
        flatten_ctes_p_profile = np.array([q/len(p_profile.columns)]*len(p_profile.columns)) # Generates new flattended profile
        flatten_ctes_p_profile = pd.DataFrame(flatten_ctes_p_profile.reshape(-1, len(flatten_ctes_p_profile)), columns=[x for x in p_profile.head()]) # pandas conversion
        ctes_discharge_hours = hoursctes(flatten_ctes_p_profile.values[0], p_profile.values[0]).ctesuse() # returns CTES discharge hours
        self.ctes_q = chargeavail(flatten_ctes_p_profile.values[0], p_profile.values[0]).unusedchiller() # Returns unused chiller space for charging CTES
        self.ctes_p = (self.ctes_q/(ctes_discharge_hours)) # power = q/time

        flatten_dict = flatten_ctes_p_profile.rename({0:'value'}, axis='index').transpose().reset_index(drop=True).rename_axis('time').reset_index().to_dict('records') # clean flatten profile for backend
        self.flatten_ctes_p_profile = [SimpleNamespace(**x) for x in flatten_dict] # returns backend ready flatten profile

        return self

