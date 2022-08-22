import json
from types import SimpleNamespace

from app.optimization import ctes_optimization, ctes_values, opt_mini, clean_input
from app.clients.webapi import api_client
from app.schemas.case_pls import CaseData
from app.clients.m_data import M_DATA_2

from random import randint, random

def get_case_data(id) -> CaseData:
    # get token
    usr = 'admin@tesapi.com'
    pwd = 'tes@dmin123'
    # api_client.get_token(usr, pwd)
    
    # get data
    # case_params = json.dumps(api_client.get_case_params(id))

    # return CaseData.parse_raw(case_params)
    return CaseData.parse_raw(json.dumps(M_DATA_2))

def main():
    id = 2
    case_data = get_case_data(id)
    load_data = case_data.load_data

    volume_limit = 100
    working_pressure = 1

    cleandata = clean_input(load_data).profile()
    no_ctes_chiller_optimization = opt_mini(case_data.params.country_selection, cleandata.nominal_load, case_data.params.safety_factor, cleandata.load_sel, cleandata.load_profile).minimize()

    # Post CTES optimizer = result
    ctes_calculation = ctes_values(no_ctes_chiller_optimization).PQ()
    M_report = SimpleNamespace(**{"lcos" : random(), "capex" : randint(0, 20000)})
    ctes_chiller_optimization = opt_mini(case_data.params.country_selection, 0, 0, 0, ctes_calculation.flatten_ctes_p_profile).minimize()

    ctes_optimizer = ctes_optimization(M_report, ctes_chiller_optimization).identify()

    # return

if __name__ == "__main__":
    res = main()
    # print(res)