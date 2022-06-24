import itertools
import uvicorn
import numpy as np
import pandas as pd
from fastapi import FastAPI, Form, Request
from fastapi.templating import Jinja2Templates
from formula import *

class minimum:
    def __init__(self, country_sel, t_in, t_out, nominal_load, safety_factor, load_sel):
        self.country_sel = country_sel
        self.t_in = t_in
        self.t_out = t_out
        self.nominal_load = nominal_load
        self.safety_factor = safety_factor
        self.load_sel = load_sel

    def best_chiller(self):
        # Declare other variables (should be user input or database info in future)
        chiller_cost_factor = 137.04 #SGD/kW must use database as this factor will clearly calculate capex proportionally to kW

        df_chiller = pd.read_csv('./Chiller_profile.csv')
        df_load = pd.read_csv('./Load_profile.csv')
        df_global = pd.read_csv('./global_data.csv')

        # df_chiller = pd.read_csv('Chiller_profile.csv')
        # df_load = pd.read_csv('Load_profile.csv')
        # df_global = pd.read_csv('global_data.csv')

        country_data = df_global.loc[df_global['country'] == self.country_sel]
        load_data = df_load.loc[df_load['load_type'] == self.load_sel]

        # Oversize the chiller to include redundancy and find different permutations
        q_perm = []
        single_chiller = safechiller(self.safety_factor, self.nominal_load).safety()
        for x in range(5):
            q_perm.append(list(c for c in itertools.combinations_with_replacement(df_chiller['round_down'], (x)) if sum(c) == single_chiller))
        
        best_chiller = permutedchiller(q_perm, df_chiller).chillerdetails()
        min_power = best_chiller['min_power']
        model = best_chiller['model']

        # Study the cooling load profile
        qload_profile = (load_data[load_data.select_dtypes(include=['number']).columns]*single_chiller).values[0]
        area_under_profile = float(integrate.trapezoid(qload_profile))
        flatten_power = np.array([area_under_profile/24]*25)
        hours_ctes = hoursctes(flatten_power, qload_profile).ctesuse()
        ctes_q = chargeavail(flatten_power, qload_profile).unusedchiller()
        ctes_p = (ctes_q/(hours_ctes))

        # Find different permutations for current sizing
        ctes_q_perm = []
        for x in range(5):
            ctes_q_perm.append(list(c for c in itertools.combinations_with_replacement(df_chiller['round_down'], (x)) if sum(c) == round(flatten_power[0], -2)))
        
        ctes_best_chiller = permutedchiller(ctes_q_perm, df_chiller).chillerdetails()
        ctes_min_power = ctes_best_chiller['min_power']
        ctes_model = ctes_best_chiller['model']

        # Tariff profile
        tariff_profile = tariffcalc(country_data).tariffprofile()

        # Chiller costing
        CAPEX = chiller_cost_factor*single_chiller
        cold_profile = load_data[load_data.select_dtypes(include=['number']).columns]*single_chiller
        elect_profile = load_data[load_data.select_dtypes(include=['number']).columns]*min_power.sum()
        energy_cost = elect_profile[elect_profile.select_dtypes(include=['number']).columns].multiply(tariff_profile)
        OPEX = float(energy_cost.sum(axis=1))
        currency = str(country_data['currency'].values[0])
        
        # CTES Chiller costing
        chiller_CAPEX = flatten_power[0]*chiller_cost_factor
        a = np.array([ctes_min_power.sum()]*25)
        chiller_cold_profile = pd.DataFrame(flatten_power.reshape(-1, len(flatten_power)), columns=[x for x in elect_profile.head()])
        chiller_elect_profile = pd.DataFrame(a.reshape(-1, len(a)), columns=[x for x in elect_profile.head()])
        chiller_energy_cost = np.array(tariff_profile)*ctes_min_power.sum()
        chiller_OPEX = chiller_energy_cost[1:].sum()

        # Plot values
        df_elect = pd.concat([elect_profile, chiller_elect_profile], ignore_index = True, axis = 0)
        df_cold = pd.concat([cold_profile, chiller_cold_profile], ignore_index = True, axis = 0)

        '''Call Tes optimizer
        tes_result = tes_optimizer(ctes_q, ctes_p)
        tes_CAPEX = tes_result['CAPEX']
        tes_OPEX = tes.result['OPEX'] # Ensure daily OPEX or multiply chiller OPEX by 365 for annual
        total_CAPEX = chiller_CAPEX + tes_CAPEX
        total_OPEX = chiller_OPEX + tes_OPEX
        return {'model': ctes_model, 'min_power': ctes_min_power, 'CAPEX': total_CAPEX, 'OPEX': total_OPEX, 'currency': currency}
        '''
        # Delete this when the above is uncommented
        return {'ctes_model': ctes_model, 'ctes_min_power': ctes_min_power, 'ctes_CAPEX': chiller_CAPEX, 'ctes_OPEX': round(chiller_OPEX,2),
        'model': model, 'min_power': min_power, 'CAPEX': CAPEX, 'OPEX': round(OPEX,2), 'currency': currency, 'df_elect': df_elect, 'df_cold': df_cold}

# Run code with arguments
# best_daily = minimum('Singapore', 29.4, 4, 8000, 0, 'on_off_peak')
# print(best_daily.best_chiller())

app = FastAPI()
templates =  Jinja2Templates('./templates/')

@app.post('/')
async def handle_form(request: Request, country: str = Form(...), tin: float = Form(...), tout: float = Form(...), nominal_load: float = Form(...), safety: float = Form(...), load_profile: str = Form(...)):
    result = minimum(country, tin, tout, nominal_load, safety, load_profile).best_chiller()
    return templates.TemplateResponse('form.html', context={'request': request, 'result': result})

@app.get("/")
async def index(request: Request):
    result = "Input values"
    return templates.TemplateResponse('form.html', context={'request': request, 'result': result})

if __name__ == '__main__':
    uvicorn.run(app, port=8000, host='0.0.0.0')
