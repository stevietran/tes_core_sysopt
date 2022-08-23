import json
from types import SimpleNamespace

from app.optimization import ctes_values, opt_mini, clean_input
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
    
    # Calculate CTES values
    ctes_calculation = ctes_values(no_ctes_chiller_optimization).PQ()

    # Get LCOC and capex for chillers with CTES
    ctes_chiller_optimization = opt_mini(case_data.params.country_selection, 0, 0, 0, ctes_calculation.flatten_ctes_p_profile).minimize()

    # Send and receive CTES values
    M_report = SimpleNamespace(**{"tes_type": "Shell and tube",

                                    "tes_attr": {

                                        "len_tube": 47.48031496062993,

                                        "num_tubes": 4,

                                        "dia_tube": 0.07314999999999999,

                                        "pitch_tube": 0.05258722385880757

                                        },

                                    "tes_op_attr": {

                                        "mdot_htf": 0.052833813640730067,

                                        "T_in_charge": -32.0,

                                        "T_out_charge": -10.0,

                                        "T_in_discharge": -10.0,

                                        "T_out_discharge": -30.0

                                        },

                                    "htf": "Nitrogen",

                                    "htf_attr": {

                                        "rho_htf": 1.13,

                                        "cp_htf": 1041.0,

                                        "k_htf": 0.0259,

                                        "mu_htf": 1.78e-05

                                        },

                                    "material": "E-22",

                                    "material_attr": {

                                        "rho_pcm": 1180.0,

                                        "cp_pcm": 3340.0,

                                        "k_pcm": 0.57

                                        },

                                    "runtime": 125.72702693939209,

                                    "lcos": 1.5331427715425923,

                                    "capex": 1818.6202707213768

                                })

    result = {"no_ctes_chiller_optimization":{"chiller_models": no_ctes_chiller_optimization.chiller_models, "chiller_capex": no_ctes_chiller_optimization.chiller_CAPEX, "chiller_lcoc": no_ctes_chiller_optimization.chiller_LCOC},
            "ctes_chiller_optimization":{"chiller_models": ctes_chiller_optimization.chiller_models, "chiller_capex": ctes_chiller_optimization.chiller_CAPEX, "chiller_lcoc": ctes_chiller_optimization.chiller_LCOC, "tes_type": M_report.tes_type, "CTES_capex": M_report.capex, "CTES_lcos": M_report.lcos}}

    return SimpleNamespace(**result)

if __name__ == "__main__":
    res = main()
    print(res)