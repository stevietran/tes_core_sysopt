import json

from app.optimization import ctes_values, opt_mini
from app.clients.webapi import api_client
from app.schemas.case_pls import CaseData
from app.schemas.tes_pls import TesOutput
from app.schemas.result_pls import ResultReturn
from app.clients.m_data import M_DATA_1
from app.clients.m_tesresult import M_report

def get_case_data(id) -> CaseData:
    # get token
    usr = 'admin@tesapi.com'
    pwd = 'tes@dmin123'
    # api_client.get_token(usr, pwd)
    
    # get data
    # case_params = json.dumps(api_client.get_case_params(id))

    # return CaseData.parse_raw(case_params)
    return CaseData.parse_raw(json.dumps(M_DATA_1))

def main():
    id = 2
    case_data = get_case_data(id) # Get case data
    params = case_data.params # Seperate params and load data
    load_data = case_data.load_data # Seperate params and load data
    country_selection = case_data.params.country_selection # Seperate country selection

    # No CTES chiller optimization
    no_ctes_chiller_optimization = opt_mini(country_selection, load_data.load_value, params.safety_factor, load_data.load_selection, load_data.load_profiles).minimize() # no ctes chiller optimiaztion (get chillers and operation strategy)
    
    # Calculate CTES values
    ctes_pq = ctes_values(no_ctes_chiller_optimization).PQ() # Get CTES P & Q values
    p_profile = ctes_pq.flatten_ctes_p_profile # Get load profile with CTES

    # CTES chiller optimization
    ctes_chiller_optimization = opt_mini(country_selection, None, 0, 0, p_profile).minimize() # Run optimization with CTES flattned profile
    ctes_pump_power = 0.03 * ctes_chiller_optimization.max_power # Returns power for pump at 3%
    
    # TES values from user, can be hardcoded but shouldn't
    working_pressure = 1 # User
    volume_limit = 100 # User
    T_out_dis = 12 # User
    T_in_dis = 5 # User
    
    # Assumed calculation values
    T_in_charge = 6.7 # Chiller minimum
    T_out_charge = 5 #?

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
    profiles = []
    for [item_ind, item] in enumerate(no_ctes_chiller_optimization.chiller_profiles['load_split_profile']):
        
        profiles_dict = {}
        profiles_dict['time'] = item['time']
        profiles_dict['load_split_profile_no_tes'] = item['value']
        profiles_dict['load_split_profile'] = ctes_chiller_optimization.chiller_profiles['load_split_profile'][item_ind]['value']
        profiles_dict["electric_split_profile_no_tes"] = no_ctes_chiller_optimization.chiller_profiles['electric_split_profile'][item_ind]['value']
        profiles_dict["electric_split_profile"] = ctes_chiller_optimization.chiller_profiles['electric_split_profile'][item_ind]['value']
        profiles_dict["cost_split_profile_no_tes"] = no_ctes_chiller_optimization.chiller_profiles['cost_split_profile'][item_ind]['value']
        profiles_dict["cost_split_profile"] = ctes_chiller_optimization.chiller_profiles['cost_split_profile'][item_ind]['value']

        profiles.append(profiles_dict)

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
            "profiles": profiles
    }
    return results

if __name__ == "__main__":
    res = main()
    print(res)