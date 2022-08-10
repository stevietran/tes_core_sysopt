import json
from optimization import opt_mini
from app.clients.webapi import api_client
from app.schemas.case_pls import CaseData

def get_case_data(id) -> CaseData:
    # get token
    usr = 'admin@tesapi.com'
    pwd = 'tes@dmin123'
    api_client.get_token(usr, pwd)
    
    # get data
    case_params = json.dumps(api_client.get_case_params(id))

    return CaseData.parse_raw(case_params)

def main():
    id = 3
    case_data = get_case_data(id)
    load_data =case_data.load_data

    country_sel = case_data.params.country_selection
    safety = case_data.params.safety_factor

    pump_power = 0
    volume_limit = 100
    working_pressure = 1

    if load_data.load_type == 'NOMIAL':
        load_sel = load_data.load_selection.lower()
        nominal_load = load_data.load_value
        load_profile = 0
    else:
        load_sel = 0
        nominal_load = 0
        load_profile = load_data.load_profiles

    optres = opt_mini(country_sel, nominal_load, safety, load_sel, load_profile, pump_power, volume_limit, working_pressure).minimize()
    
    return optres

if __name__ == "__main__":
    res =main()
    print(res)
