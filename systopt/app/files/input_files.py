import os.path as path

main_path = path.dirname(path.abspath(__file__))

chiller_file_dir = path.join(main_path, "chiller_curves.csv")
global_data_dir = path.join(main_path, "global_data.csv")
load_profile_dir = path.join(main_path, "load_profile.csv")