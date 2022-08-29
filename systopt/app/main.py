import json
from types import SimpleNamespace

from app.optimization import ctes_values, opt_mini
from app.clients.webapi import api_client
from app.schemas.case_pls import CaseData
from app.schemas.tes_pls import TesOutput
from app.schemas.result_pls import ResultReturn
from app.clients.m_data import M_DATA_2
from app.clients.m_tesresult import M_report
from app.clients.m_result import M_DATA_RESULT

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
    params = case_data.params
    load_data = case_data.load_data
    country_selection = case_data.params.country_selection

    # No CTES chiller optimization
    no_ctes_chiller_optimization = opt_mini(country_selection, load_data.load_value, params.safety_factor, load_data.load_selection, load_data.load_profiles).minimize()
    
    # Calculate CTES values
    ctes_pq = ctes_values(no_ctes_chiller_optimization).PQ()
    p_profile = ctes_pq.flatten_ctes_p_profile

    # CTES chiller optimization
    ctes_chiller_optimization = opt_mini(country_selection, None, 0, 0, p_profile).minimize()
    ctes_pump_power = 0.03 * ctes_chiller_optimization.max_power
    
    # TES values from user, can be hardcoded but shouldn't
    working_pressure = 1
    volume_limit = 100
    T_out_dis = 6.7
    T_in_charge = T_out_dis - 2
    
    # Assumed calculation values
    T_in_dis = 5#
    T_out_charge = 5#

    # TES input values
    tes_input = {"working_pressure": working_pressure,
                "volume_limit": volume_limit,
                "power_dis": ctes_pq.ctes_p,
                "energy_dis": ctes_pq.ctes_q,
                "power_pump": ctes_pump_power,
                "T_in_charge": T_in_charge,
                "T_out_charge": T_out_charge,
                "T_in_dis": T_in_dis,
                "T_out_dis": T_out_dis,
                "selected_toxicity_level": "None",
                "phase": "All",
                "accurancy_level": params.accuracy_level
                } 
    
    tes_output = TesOutput.parse_raw(json.dumps(M_report))

    # TODO: Prepare data for Web backend
    results = {"result_data": {
                                "tes_type": tes_output.tes_type,
                                "tes_attr": tes_output.tes_attr,
                                "tes_op_attr": tes_output.tes_op_attr,
                                "chiller": ctes_chiller_optimization.chiller_models,
                                "chiller_no_tes": no_ctes_chiller_optimization.chiller_models,
                                "capex": ctes_chiller_optimization.chiller_CAPEX,
                                "capex_no_tes": no_ctes_chiller_optimization.chiller_CAPEX,
                                "lcos": ctes_chiller_optimization.chiller_LCOC,
                                "lcos_no_tes": no_ctes_chiller_optimization.chiller_LCOC,
                                "htf": tes_output.htf,
                                "htf_attr": tes_output.htf_attr,
                                "material": tes_output.material,
                                "material_attr": tes_output.material_attr,
                                "tes_capex": tes_output.capex,
                                "tes_lcos": tes_output.lcos,
                                "runtime": tes_output.runtime 
                            },
            "load_split_profile_no_tes": no_ctes_chiller_optimization.chiller_profiles['load_split_profile'],
            "load_split_profile": ctes_chiller_optimization.chiller_profiles['load_split_profile'],
            "electric_split_profile_no_tes": no_ctes_chiller_optimization.chiller_profiles['electric_split_profile'],
            "electric_split_profile": ctes_chiller_optimization.chiller_profiles['electric_split_profile'],
            "cost_split_profile_no_tes": no_ctes_chiller_optimization.chiller_profiles['cost_split_profile'],
            "cost_split_profile": ctes_chiller_optimization.chiller_profiles['cost_split_profile']
            }

    return results

if __name__ == "__main__":
    res = main()
    print(res)