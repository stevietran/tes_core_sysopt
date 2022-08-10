from optimization import opt_mini
from app.clients.webapi import api_client

id = 2

def test_get_token():
    usr = 'admin@tesapi.com'
    pwd = 'tes@dmin123'
    res = api_client.get_token(usr, pwd)

test_get_token()

case_params = api_client.get_case_params(id)

params = case_params['params']
load_data = case_params['load_data']

country_sel = params['country_selection']
safety = params['safety_factor']

pump_power = 0
volume_limit = 0
working_pressure = 0

if load_data['load_type'] == 'NOMIAL':
    load_sel = load_data['load_selection'].lower()
    nominal_load = load_data['load_value']
    load_profile = 0
else:
    load_sel = 0
    nominal_load = 0
    load_profile = load_data['load_profiles']

optres = opt_mini(country_sel, nominal_load, safety, load_sel, load_profile, pump_power, volume_limit, working_pressure).minimize()

# # Organize data
# chillers = ' '.join(list(optres['ctes_models']))
# no_ctes_chillers = ' '.join(list(optres['no_ctes_models']))

# numchillers =  len(optres['ctes_models'])
# no_ctes_numchillers = len(optres['no_ctes_models'])

# no_str_profiles = optres['no_ctes_profiles'].drop(['model','type'], axis=1)

# totalrows = len(no_str_profiles.index)

# keylist = []
# for x in range(numchillers):
#     temp = 'value' + str(x + 1)
#     keylist.append(temp)

# keylist = (keylist*3)
# keylist.insert(0, 'time')

# cleanprof = no_str_profiles.transpose().rename_axis('time').reset_index()
# cleanprof.iloc[0] = keylist
# print(cleanprof)
    
# post_res = {
#   "result_data": {
#       "tes_type": "SNT",
#       "tes_attr": {
#           "mass": 10,
#           "length": 200,
#           "height": 20
#       },
#       "tes_op_attr": {
#           "power": 10,
#           "pressure": 100,
#           "flowrate": 4            
#       },
#       "chiller": chillers,
#       "chiller_no_tes": no_ctes_chillers,
#       "capex": optres['ctes_CAPEX'],
#       "capex_no_tes": optres['no_ctes_CAPEX'],
#       "lcos": optres['ctes_OPEX'],
#       "lcos_no_tes": optres['no_ctes_OPEX'],
#       "htf": "Ar",
#       "htf_attr": {
#           "density": 10,
#           "c_p": 1005           
#       },
#       "material": "RM-11",
#       "material_attr": {
#           "density": 10,
#           "phase": "Liquid"
#       },
#       "cost": 1900,
#       "run_time": 1200 
#   },
  
#   "load_split_profile": [
#       {
#           "time": 100,
#           "value": 0
#       },
#       {
#           "time": 8,
#           "value": 10
#       },
#       {
#           "time": 16,
#           "value": 10
#       },
#       {
#           "time": 24,
#           "value": 0
#           "value2":0
#       }
#   ],
#   "electric_split_profile": [
#   {
#     "time": 0,
#     "value": 0
#   },
#   {
#     "time": 8,
#     "value": 10
#   },
#   {
#     "time": 16,
#     "value": 10
#   },
#   {
#     "time": 24,
#     "value": 0
#   }
# ],
#   "cost_profile": [
#     {
#       "time": 0,
#       "value": 0
#     },
#     {
#       "time": 8,
#       "value": 10
#     },
#     {
#       "time": 16,
#       "value": 10
#     },
#     {
#       "time": 24,
#       "value": 0
#     }
#   ]
# }

# postjob = api_client.post_result(post_res, id)
# print(postjob)