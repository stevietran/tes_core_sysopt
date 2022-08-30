import json

from app.clients.webapi import api_client
from app.optimization import ctes_values, opt_mini
from app.schemas.tes_pls import TesOutput

class OptPls():
    def __init__(self, case_id: int, task_id: str) -> None:
        self.task_id = task_id
        # Get case data
        case_data =api_client.get_case_data(case_id)
        self.params = case_data.params
        self.load_data = case_data.load_data
        
        self.no_ctes_opt : opt_mini = self.optimise_no_tes()
        
        self.ctes_opt : opt_mini = self.optimise()
    
    def optimise_no_tes(self, ) -> json:
        # No CTES chiller optimization
        no_ctes_opt = opt_mini(
            self.params.country_selection, 
            self.load_data.load_value, 
            self.params.safety_factor, 
            self.load_data.load_selection, 
            self.load_data.load_profiles
            ).minimize()

        return no_ctes_opt
    
    def optimise(self):
        # Calculate CTES values
        ctes_pq : ctes_values = ctes_values(self.no_ctes_opt).PQ()
        p_profile = ctes_pq.flatten_ctes_p_profile

        self.ctes_p = ctes_pq.ctes_p
        self.ctes_q = ctes_pq.ctes_q
        
        # CTES chiller optimization
        ctes_opt = opt_mini(
            self.params.country_selection, 
            None, 
            0, 
            0, 
            p_profile
            ).minimize()
        
        return ctes_opt
    
    def get_tes_input(self):
        # Prepare TES input
        ctes_pump_power = 0.03 * self.ctes_opt.max_power
        working_pressure = 1
        volume_limit = 100
        T_out_dis = 10
        T_in_charge = T_out_dis - 2
        
        # Assumed calculation values
        T_in_dis = 30#
        T_out_charge = 30#

        # TES input values
        tes_input = {
            "working_pressure": working_pressure,
            "volume_limit": volume_limit,
            "power_dis": self.ctes_p,
            "energy_dis": self.ctes_q,
            "power_pump": ctes_pump_power,
            "T_in_charge": T_in_charge,
            "T_out_charge": T_out_charge,
            "T_in_dis": T_in_dis,
            "T_out_dis": T_out_dis,
            "selected_toxicity_level": "None",
            "phase": "All",
            "accurancy_level": self.params.accuracy_level
        } 
        
        return tes_input
    
    def get_case_result(self, tes_report: json):
        tes_output:TesOutput = TesOutput.parse_raw(tes_report)

        # TODO: Prepare data for Web backend

        results = {
            "result_data": {
                "tes_type": tes_output.tes_type,
                "tes_attr": tes_output.tes_attr,
                "tes_op_attr": tes_output.tes_op_attr,
                "chiller": self.ctes_opt.chiller_models,
                "chiller_no_tes": self.no_ctes_opt.chiller_models,
                "capex": self.ctes_opt.chiller_CAPEX + tes_output.capex,
                "capex_no_tes": self.no_ctes_opt.chiller_CAPEX,
                "lcos": self.ctes_opt.chiller_LCOC + tes_output.lcos,
                "lcos_no_tes": self.no_ctes_opt.chiller_LCOC,
                "htf": tes_output.htf,
                "htf_attr": tes_output.htf_attr,
                "material": tes_output.material,
                "material_attr": tes_output.material_attr,
                "run_time": tes_output.runtime 
            },
            "load_split_profile_no_tes": self.no_ctes_opt.chiller_profiles['load_split_profile'],
            "load_split_profile": self.ctes_opt.chiller_profiles['load_split_profile'],
            "electric_split_profile_no_tes": self.no_ctes_opt.chiller_profiles['electric_split_profile'],
            "electric_split_profile": self.ctes_opt.chiller_profiles['electric_split_profile'],
            "cost_split_profile_no_tes": self.no_ctes_opt.chiller_profiles['cost_split_profile'],
            "cost_split_profile": self.ctes_opt.chiller_profiles['cost_split_profile']
        }
        return results
