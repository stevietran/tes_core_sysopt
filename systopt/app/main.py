import uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.templating import Jinja2Templates
from support import *

class opt_mini:
    def __init__(self, country_sel, tin, tout, nominal_load, safety, load_sel, pump_power, volume_limit, working_pressure):
        self.country_sel = country_sel
        self.tin = tin
        self.tout = tout
        self.nominal_load = nominal_load
        self.safety = safety
        self.load_sel = load_sel
        self.pump_power = pump_power
        self.volume_limit = volume_limit
        self.working_pressure = working_pressure

    def minimize(self):
        # Import data 
        dataimp = dataimport(self.country_sel, self.load_sel).seldata()
        df_curves = dataimp['df_curves']
        country_data = dataimp['country_data']
        load_data = dataimp['load_data']
        chiller_cost_factor = dataimp['chiller_cost_factor']
        
        # Currency selection
        currency = str(country_data['currency'].values[0])

        # Oversize chiller if needed
        oversized_chiller = safechiller(self.safety, self.nominal_load).chiller_size()

        # Tariff Profile
        tariff_profile = tariffcalc(country_data).tariffprofile()
        
        # Study the load profile and flatten for CTES
        no_ctes_p_profile = (load_data[load_data.select_dtypes(include=['number']).columns]*oversized_chiller)
        no_ctes_q = areaUnder(no_ctes_p_profile.values[0]).curve()
        flatten_ctes_p_profile = np.array([no_ctes_q/24]*25)
        flatten_ctes_p_profile = pd.DataFrame(flatten_ctes_p_profile.reshape(-1, len(flatten_ctes_p_profile)), columns=[x for x in no_ctes_p_profile.head()])
        ctes_discharge_hours = hoursctes(flatten_ctes_p_profile.values[0], no_ctes_p_profile.values[0]).ctesuse()
        
        # Send to TES Optimizer
        """
        ctes_q = chargeavail(flatten_ctes_p_profile.values[0], no_ctes_p_profile.values[0]).unusedchiller() 
        ctes_p = (ctes_q/(ctes_discharge_hours))
        pump_power = self.pump_power
        volume_limit = self.volume_limit
        working_pressure = self.working_pressure
        """
        
        # Get the chiller models and profiles
        no_ctes_lowest_chiller_model = chillselect(df_curves, oversized_chiller).select()
        no_ctes_chiller_profiles = chillprof(df_curves, no_ctes_lowest_chiller_model, no_ctes_p_profile).prof()
        no_ctes_all_profiles = costingprof(tariff_profile, no_ctes_chiller_profiles).costprof()

        ctes_lowest_chiller_model = chillselect(df_curves, flatten_ctes_p_profile.values[0].max()).select()
        ctes_chiller_profiles = chillprof(df_curves, ctes_lowest_chiller_model, flatten_ctes_p_profile).prof()
        ctes_all_profiles = costingprof(tariff_profile, ctes_chiller_profiles).costprof()

        # Get total daily cost of setup
        no_ctes_capex = chiller_cost_factor*oversized_chiller
        no_ctes_daily_opex = totaldaycost(no_ctes_all_profiles).dailyopex()
        ctes_capex = chiller_cost_factor*flatten_ctes_p_profile.values[0].max()
        ctes_daily_opex = totaldaycost(ctes_all_profiles).dailyopex()

        return {'no_ctes_profiles': no_ctes_all_profiles,
                'no_ctes_models': no_ctes_all_profiles.loc[no_ctes_all_profiles['type'] == 'cooling_load']['model'].values[:],
                'no_ctes_CAPEX': round(no_ctes_capex, 2),
                'no_ctes_OPEX': round(no_ctes_daily_opex, 2),
                'ctes_profiles': ctes_all_profiles,
                'ctes_models': ctes_all_profiles.loc[ctes_all_profiles['type'] == 'cooling_load']['model'].values[:],
                'ctes_CAPEX': round(ctes_capex, 2),
                'ctes_OPEX': round(ctes_daily_opex, 2),
                'currency': currency
                }

app = FastAPI()
templates =  Jinja2Templates('./templates/')

@app.post('/')
async def handle_form(request: Request, country: str = Form(...), tin: float = Form(...), tout: float = Form(...), nominal_load: float = Form(...), safety: float = Form(...), load_profile: str = Form(...), pump_power: float = Form(...), volume_limit: float = Form(...),  working_pressure: float = Form(...)):
    result = opt_mini(country, tin, tout, nominal_load, safety, load_profile, pump_power, volume_limit, working_pressure).minimize()
    return templates.TemplateResponse('form.html', context={'request': request, 'result': result})

@app.get("/")
async def index(request: Request):
    result = "Input values"
    return templates.TemplateResponse('form.html', context={'request': request, 'result': result})

if __name__ == '__main__':
    uvicorn.run(app, port=8000, host='0.0.0.0')