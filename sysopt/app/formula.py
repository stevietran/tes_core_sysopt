import math
import numpy as np
import pandas as pd
from scipy import integrate

# Calculate Wet Bulb Temperature (future when we consider cooling tower)
class wetBulbCalc:
    def __init__(self, T_ambient, relH):
        self.T_ambient = T_ambient
        self.relH = relH

    def wetBulb(self):
        T_wet = self.T_ambient * math.atan(0.151977 * (self.relH + 8.313659)**(1/2)) + math.atan(self.T_ambient + self.relH)
        - math.atan(self.relH - 1.676331) + 0.00391838 * (self.relH)**(3/2) * math.atan(0.023101 * self.relH) - 4.686035
        
        return round(T_wet, 2)

# Caculate cold power with safety factor
class safechiller:
    def __init__(self, safety_factor, nominal_load):
        self.safety_factor = safety_factor
        self.nominal_load = nominal_load

    def safety(self):
        if self.safety_factor == 0:
            sized_chiller = self.nominal_load
        else:
            sized_chiller = self.nominal_load * (1 + (self.safety_factor/100))
        
        return sized_chiller

# Identify minimum chiller with the details
class permutedchiller:
    def __init__(self, q_perm, df_chiller):
        self.q_perm = q_perm
        self.df_chiller = df_chiller
    
    def chillerdetails(self):
       # Filter out empty elements
        q_filt = []
        q_filt = list(filter(lambda x: len(x)!=0, self.q_perm))

        # Identify the details used for each permutation
        p_all = []
        a = 0
        for x in q_filt:
            b=0
            outside = []
            for y in x:
                inside = []
                for z in range(len(y)):
                    p_iter = self.df_chiller.loc[self.df_chiller["round_down"] == x[b][z], "power_input"].values[0]
                    inside.append(p_iter)
                outside.insert(b, np.array(inside))
                b+=1
            p_all.insert(a, outside)
            a+=1
        
        # Identify the minimum power used
        min = []
        for x in p_all:
            xarray = np.array(x)
            min.append(xarray[xarray.sum(axis=1).argmin()])

        min_power = min[0]
        for x in range(len(min)):
            if (min[x].sum()) < min_power.sum():
                min_power = min[x]

        # Identify chiller model
        model = []
        c = 0
        for x in min_power:
            model_iter = self.df_chiller.loc[self.df_chiller["power_input"] == x, "Model"].values[0]
            model.append(model_iter)

        return {'model': model, 'min_power': min_power}

# Calculate available charge after shifting load
class chargeavail:
    def __init__(self, flatten_power, qload_profile):
        self.qload_profile = qload_profile
        self.flatten_power = flatten_power

    def unusedchiller(self):
        avail_charge = []
        i=0

        for x in self.qload_profile:
            if x < self.flatten_power[i]:
                avail_charge.append(float(self.flatten_power[i]-x))
            else:
                avail_charge.append(0.0)

        return float(integrate.trapezoid(avail_charge))

# Calculate number of hours discharging CTES
class hoursctes:
    def __init__(self, flatten_power, qload_profile):
        self.qload_profile = qload_profile
        self.flatten_power = flatten_power

    def ctesuse(self):
        avail_charge = []
        i=0

        for x in self.qload_profile:
            if x < self.flatten_power[i]:
                avail_charge.append(float(self.flatten_power[i]-x))
            else:
                avail_charge.append(0.0)

        return float(avail_charge.count(0))

# generate tariff profile to be used for OPEX calculations
class tariffcalc:
    def __init__(self, country_data):
        self.country_data = country_data
    
    def tariffprofile(self):
        tariff_profile = []
        for i in range(0, 2500, 100):
            if i < self.country_data['non_peak_end'].values:
                tariff_profile.append(float(self.country_data['non_peak_tariff'].values))
            elif (i < self.country_data['non_peak_start'].values):
                tariff_profile.append(float(self.country_data['peak_tariff'].values))
            else:
                tariff_profile.append(float(self.country_data['non_peak_tariff'].values))
        
        return tariff_profile
