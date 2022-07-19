import warnings
import math
import numpy as np
import pandas as pd
from scipy import integrate
from scipy.optimize import basinhopping, NonlinearConstraint, differential_evolution

# Calculate Wet Bulb Temperature (future when we consider cooling tower)
class wetBulbCalc:
    def __init__(self, T_ambient, relH):
        self.T_ambient = T_ambient
        self.relH = relH

    def wetBulb(self):
        T_wet = self.T_ambient * math.atan(0.151977 * (self.relH + 8.313659)**(1/2)) + math.atan(self.T_ambient + self.relH)
        - math.atan(self.relH - 1.676331) + 0.00391838 * (self.relH)**(3/2) * math.atan(0.023101 * self.relH) - 4.686035
        
        return round(T_wet, 2)

class areaUnder:
    def __init__(self, profile):
        self.profile = profile
    
    def curve(self):
        return float(integrate.trapezoid(self.profile))

# Import data
class dataimport:
    def __init__(self, country_sel, load_sel):
        self.country_sel = country_sel
        self.load_sel = load_sel
    
    def seldata(self):
        chiller_cost_factor = 137.04 #SGD/kW must use database as this factor will clearly calculate capex proportionally to kW

        df_load = pd.read_csv("./files/Load_profile.csv")
        df_global = pd.read_csv("./files/global_data.csv")
        df_curves = pd.read_csv("./files/chiller_curves.csv")

        country_data = df_global.loc[df_global['country'] == self.country_sel]
        load_data = df_load.loc[df_load['load_type'] == self.load_sel]

        return {'chiller_cost_factor': chiller_cost_factor, 'df_curves': df_curves, 'country_data': country_data, 'load_data': load_data}

# Caculate cold power with safety factor
class safechiller:
    def __init__(self, safety, nominal_load):
        self.safety = safety
        self.nominal_load = nominal_load

    def chiller_size(self):
        if self.safety == 0:
            sized_chiller = self.nominal_load
        else:
            sized_chiller = self.nominal_load * (1 + (self.safety/100))
        
        return sized_chiller

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

# Find Chillers
class chillselect:
    def __init__(self,  df_curves, oversized_chiller):
        self.df_curves = df_curves
        self.oversized_chiller = oversized_chiller

    def select(self):
        warnings.filterwarnings("ignore", message="delta_grad == 0.0. Check if the approximated function is linear. If the function is linear better results can be obtained by defining the Hessian as zero instead of using quasi-Newton approximations.")
        counter = len(self.df_curves.index)
        split_load = []
        total_power = str()

        def objective_func(split_load, df_curves, cooling_loads):
            args = df_curves, cooling_loads
            total_power = str()
            i=0
            for x in df_curves['cop_curve']:
                total_power = total_power + ' + ' + x
                total_power = total_power.replace('[i]','[' + str(i) +']')
                i+=1
            return (eval(total_power))

        def constraint1(split_load):
            return split_load.sum()

        bnds = list()
        for x in self.df_curves['max_cooling_load']:
            b = (0.0, float(x))
            bnds.append(b)

        for x in range(counter):
            test_load = self.oversized_chiller/counter
            split_load.append(test_load)

        split_power = []
        model = []
        nlc = NonlinearConstraint(constraint1, self.oversized_chiller-0.0001, self.oversized_chiller)
        minimizer_kwargs = {'args':(self.df_curves, self.oversized_chiller), 'method':'trust-constr', 'constraints':nlc, 'bounds':bnds, 'tol':1e-5}

        solution = basinhopping(objective_func, split_load, minimizer_kwargs=minimizer_kwargs, niter=200, seed=1, stepsize=0.01)
        # solution = differential_evolution(func=objective_func, bounds=bnds, args=(self.df_curves, self.oversized_chiller), seed=1, constraints=(nlc), disp=False)
        
        split_load = solution.x
        split_load = [0 if i<0.001 else i for i in split_load]

        i=0
        for y in self.df_curves['cop_curve']:
                total_power = y
                total_power = total_power.replace('[i]','[' + str(i) +']')
                temp = eval(total_power)
                split_power.append(temp)
                i+=1

        i=0
        for z in split_power:
            if z > 2.51:
                temp = self.df_curves['Model'][i]
            else:
                temp = 0
            model.append(temp)
            i+=1
        
        model = [i for i in model if i != 0]
        return model

# Chiller Profiles
class chillprof:
    def __init__(self, df_curves, model, load_profile):
        self.df_curves = df_curves
        self.model = model
        self.load_profile = load_profile

    def prof(self):
        warnings.filterwarnings("ignore", message="delta_grad == 0.0. Check if the approximated function is linear. If the function is linear better results can be obtained by defining the Hessian as zero instead of using quasi-Newton approximations.")
        location = pd.DataFrame()
        total_power = str()
        power_prof = pd.DataFrame()

        def objective_func(split_load, location, cooling_loads):
            args = location, cooling_loads
            total_power = str()
            i=0
            for t in location['cop_curve']:
                total_power = total_power + ' + ' + t
                total_power = total_power.replace('[i]','[' + str(i) +']')
                i+=1
            return (eval(total_power))

        def constraint1(split_load):
            return split_load.sum()

        for x in self.model:
            temp = self.df_curves.loc[self.df_curves['Model'] == x]
            temp2 = temp.drop_duplicates(keep='first')
            location = pd.concat([location, temp2], ignore_index=True)

        bnds = list()
        for y in location['max_cooling_load']:
            b = (0.0, float(y))
            bnds.append(b)

        for x in self.load_profile:
            split_power = []
            model2 = []
            outtype = []
            cooling_load = self.load_profile[x].values[0]
            nlc = NonlinearConstraint(constraint1, cooling_load-0.0001, cooling_load)
            solution = differential_evolution(func=objective_func, bounds=bnds, args=(location, cooling_load), seed=1, constraints=(nlc), disp=False, tol=1e-5)

            split_load = solution.x

            i=0
            for z in location['cop_curve']:
                total_power = z
                total_power = total_power.replace('[i]','[' + str(i) +']')
                temp = eval(total_power)
                split_power.append(temp)
                temp2 = location['Model'][i]
                model2.append(temp2)
                if (i % 2) == 0:
                    hold = 'cooling_load'
                else:
                    hold = 'input_power'
                outtype.append(hold)
                i+=1

            if x == '0':
                temp3 = pd.DataFrame({'model': model2, 'type': 'cooling_load', str(x): split_load})
                temp4 = pd.concat([temp3, pd.DataFrame({'model': model2, 'type': 'input_power', str(x): split_power})])
                power_prof = pd.concat([power_prof, temp4], axis=1).round(2)

            else:
                temp3 = pd.DataFrame({str(x): split_load})
                temp4 = pd.concat([temp3, pd.DataFrame({str(x): split_power})])
                power_prof = pd.concat([power_prof, temp4], axis=1).round(2)

        power_prof = power_prof.loc[power_prof.sum(axis=1, numeric_only=True) != 0]
            
        return power_prof

# Daily cost profile
class costingprof:
    def __init__(self, tariff_profile, profiles):
        self.tariff_profile = tariff_profile
        self.profiles = profiles

    def costprof(self):
        elec_prof = self.profiles.loc[self.profiles['type'] == 'input_power']
        elec_prof = elec_prof.replace('input_power','energy_cost') 
        elec_cost = elec_prof[elec_prof.select_dtypes(include=['number']).columns].multiply(self.tariff_profile).round(2)
        elec_cost = pd.concat([elec_prof['model'], elec_prof['type'], elec_cost], axis=1) 
        chiller_profiles =  pd.concat([self.profiles ,elec_cost])

        return chiller_profiles

# Total daily cost
class totaldaycost:
    def __init__(self, profiles):
        self.profiles = profiles
    
    def dailyopex(self):
        daily_cost_prof = self.profiles.loc[self.profiles['type'] == 'energy_cost']
        daily_cost_prof = daily_cost_prof.iloc[:, 2:].apply(lambda g: integrate.trapezoid(g), axis=1)
        total_daily_cost = daily_cost_prof.sum()

        return total_daily_cost