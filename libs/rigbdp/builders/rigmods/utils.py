import importlib, json
# from maya import cmds, mel

import rpdecorator
from rigbdp.build import build_utils as rig_utils
from rigbdp.import_export import sdk_utils, corrective
from rigbdp.build import post_scripts, rigbuild_mini

# Step 1: Create a list of modules
TMP = [
    rig_utils,
    sdk_utils,
    corrective,
    post_scripts,
    rigbuild_mini,
    rpdecorator,
]

# Step 2: Create __all__ for module names
__all__ = [module.__name__ for module in TMP]

# Step 3: Update globals to include the modules
globals().update({module.__name__: module for module in TMP})

def reload_all():
    for mod in TMP:
        importlib.reload(mod)
reload_all()
# Example usage (after importing this module):
# from your_module import * 
# You can now directly access functions and classes from utils, sdk_utils, corrective, post_scripts, rigbuild_mini

# @rpdecorator.print_bookends
def print_dict_as_code(dictionary):
    for key, value in dictionary.items():
        if isinstance(value, str):
            # Use raw string notation for paths or strings with backslashes
            if '\\' in value:
                print(f"{key} = r'{value}'")
            else:
                print(f"{key} = '{value}'")
        elif isinstance(value, list):
            # Handle lists with mixed types
            formatted_list = []
            for item in value:
                if isinstance(item, str):
                    if '\\' in item:
                        formatted_list.append(f"r'{item}'")
                    else:
                        formatted_list.append(f"'{item}'")
                else:
                    formatted_list.append(str(item))
            formatted_list_str = ',\n                  '.join(formatted_list)
            print(f"{key} = [{formatted_list_str}]")
        else:
            # For integers, floats, and other types, just print them as-is
            print(f"{key} = {value}")

# # Example usage
# data = {
#     'MnM_rig_path': 'C:\\Users\\harri\\Documents\\BDP\\build_demo\\jsh\\input\\jsh_RIG_200_v008_MnM.ma',
#     'SHAPES_mel_paths': [
#         'C:\\Users\\harri\\Documents\\BDP\\build_demo\\jsh\\SHAPES\\M_jsh_base_body_geoShapes_blendShape.mel',
#         'C:\\Users\\harri\\Documents\\BDP\\build_demo\\jsh\\SHAPES\\M_jsh_base_cloth_top_fabric_geoShapes_blendShape.mel',
#         'C:\\Users\\harri\\Documents\\BDP\\build_demo\\jsh\\SHAPES\\test_mel_file.mel'
#     ],
#     'version': 1,
#     'description': 'Project config file',
#     'scale': 0.75,
#     'this': False,
#     'custom_dict': {'new_this':False, 'other_this':['something', 'something else']}
# }

# print_dict_as_code(data)
