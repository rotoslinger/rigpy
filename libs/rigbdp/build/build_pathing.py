import os, importlib, glob
from functools import wraps

from rigbdp.builders.rigmods import utils as builder_utils


def print_bookends(func):
    """
    Decorator to print bookend lines before and after the output of the function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        print('\n########################################### BUILDER PATHS ##########################################')
        func(*args, **kwargs)
        print('####################################################################################################\n')
    return wrapper



def create_char_path_verbose(path):
    if not os.path.exists(path): 
        os.makedirs(path, exist_ok=True)  # Create the character base directory
        print(f'Path created: {path}')
    else: print(f'Path already exists: {path}')

def create_char_structure(char_name, dir_to_char, ):
    """
    Creates the necessary directory structure for the character, but does not create any files.

    Args:
        dir_to_char (str): The base directory where the character structure should be created.
        char_name (str): The character name, which will create subdirectories for that character.

    Returns:
        dict: Dictionary with paths of created directories for the character.
    """
    sep = os.path.sep
    
    # Construct base paths
    char_base_dir = rf'{dir_to_char}{sep}{char_name}{sep}'  # For example: C:\Users\harri\Documents\BDP\cha\jsh\
    SHAPES_dir = rf'{char_base_dir}SHAPES{sep}'  # SHAPES directory for storing MEL files
    output_dir = rf'{char_base_dir}output{sep}'  # Output directory for output files
    input_dir = rf'{char_base_dir}input{sep}'  # Output directory for output files
    
    # Create the directories if they don't already exist
    create_char_path_verbose(char_base_dir)  # Create the character base directory
    create_char_path_verbose(SHAPES_dir)  # Create SHAPES directory
    create_char_path_verbose(output_dir)  # Create output directory
    create_char_path_verbose(input_dir)  # Create input directory

    return_dict = {'char_base_dir': char_base_dir,
                   'SHAPES_dir': SHAPES_dir,
                   'output_dir': output_dir,
                   'input_dir': input_dir
                   }

    # Return a dictionary with the paths of the created directories
    return return_dict


# # Example usage
# char_name = 'jsh'
# dir_to_char = r'C:\Users\harri\Documents\BDP\cha'
# create_char_structure(char_name=char_name, dir_to_char=dir_to_char )
print('IMPORTING')
@print_bookends
def find_files(char_name, dir_to_char, new_version_number,
               input_extension='.ma', ):
    """
    Finds specific files based on extensions in a character's directory structure.

    Args:
        char_dir (str): The base directory where the character data is stored.
        char_name (str): Character name to build paths dynamically.
        new_version (int): Version number to format the output filename.
        MnM_extension (str): The file extension for the MnM build file.
        SHAPES_extension (str): The file extension for SHAPES MEL files.
        sdk_filename (str): The name of the sdk data file.

    Returns:
        dict: Dictionary with paths for MnM rig, SHAPES MEL files, output, and sdk data.
    """
    sep = os.path.sep
    SHAPES_extension='.mel'
    sdk_filename='sdk_data.json'
    # Constructing the dynamic character directory and other subdirectories
    dir_to_char = rf'{dir_to_char}{sep}{char_name}{sep}'
    SHAPES_dir = rf'{dir_to_char}SHAPES{sep}'
    output_dir = rf'{dir_to_char}output{sep}'
    input_dir = rf'{dir_to_char}input{sep}'
    # Find all files with the specified MnM and SHAPES extensions in their directories
    input_rig_path = glob.glob(f'{input_dir}*{input_extension}')
    if not input_rig_path: input_rig_path= glob.glob(f'{input_dir}*.mb')
    SHAPES_mel_paths = glob.glob(f'{SHAPES_dir}*{SHAPES_extension}')
    
    # Construct output filename based on character name and version
    output_filename = f'{char_name}_RIG_200_v{new_version_number:03}.ma'
    build_output_path = f'{output_dir}{output_filename}'

    # Path for sdk data file
    sdk_data_path = rf'{input_dir}{sdk_filename}'
    
    return_dict = {'char_name': char_name,
                   'input_rig_path': input_rig_path[0] if input_rig_path else None,
                   'SHAPES_mel_paths': SHAPES_mel_paths,
                   'build_output_path': build_output_path,
                   'sdk_data_path': sdk_data_path,
                   }

    print('# Copy these paths to your builder')
    builder_utils.print_dict_as_code(return_dict)
    # Return a dictionary with all found file paths
    return return_dict



def return_found_files(char_name, dir_to_char, new_version_number):
    """
    Finds specific files based on extensions in a character's directory structure.

    Args:
        char_dir (str): The base directory where the character data is stored.
        char_name (str): Character name to build paths dynamically.
        new_version (int): Version number to format the output filename.
        MnM_extension (str): The file extension for the MnM build file.
        SHAPES_extension (str): The file extension for SHAPES MEL files.
        sdk_filename (str): The name of the sdk data file.

    Returns:
        dict: Dictionary with paths for MnM rig, SHAPES MEL files, output, and sdk data.
    """
    input_extension = '.ma'
    sep = os.path.sep
    SHAPES_extension='.mel'
    sdk_filename='sdk_data.json'
    # Constructing the dynamic character directory and other subdirectories
    dir_to_char = rf'{dir_to_char}{sep}{char_name}{sep}'
    SHAPES_dir = rf'{dir_to_char}SHAPES{sep}'
    output_dir = rf'{dir_to_char}output{sep}'
    input_dir = rf'{dir_to_char}input{sep}'
    # Find all files with the specified MnM and SHAPES extensions in their directories
    input_rig_path = glob.glob(f'{input_dir}*{input_extension}')
    if not input_rig_path: input_rig_path= glob.glob(f'{input_dir}*.mb')
    SHAPES_mel_paths = glob.glob(f'{SHAPES_dir}*{SHAPES_extension}')
    bs_connection_maps = glob.glob(f"{input_dir}BsConnMap_*")
    # Construct output filename based on character name and version
    output_filename = f'{char_name}_RIG_200_v{new_version_number:03}.ma'
    build_output_path = f'{output_dir}{output_filename}'

    # Path for sdk data file
    sdk_data_path = rf'{input_dir}{sdk_filename}'
    
    return_dict = {'char_name': char_name,
                   'input_rig_path': input_rig_path[0] if input_rig_path else None,
                   'SHAPES_mel_paths': SHAPES_mel_paths,
                   'build_output_path': build_output_path,
                   'sdk_data_path': sdk_data_path,
                   'bs_connection_maps': bs_connection_maps,
                   }
    # Return a dictionary with all found file paths
    return return_dict



# Example usage
# char_name = 'jsh'
# dir_to_char = r'C:\Users\harri\Documents\BDP\cha'
# new_version = 11
# file_paths = find_files(char_name=char_name, dir_to_char=dir_to_char, new_version=new_version)


# def manual_path_building():
#     sep = os.path.sep
#     char_name = 'jsh'
#     new_version = 11
#     char_dir= rf'C:\Users\harri\Documents\BDP\cha'
#     SHAPES_dir_name = 'SHAPES'
#     SHAPES_mel_filenames = ['M_jsh_base_body_geoShapes_blendShape.mel',
#                             'M_jsh_base_cloth_top_fabric_geoShapes_blendShape']
#     sdk_filename = 'sdk_data.json'
#     output_dir_name = 'output'
#     MnM_build_file = 'jsh_RIG_200_v008_MnM.ma'

#     ### class args to be dynamically created:
#     # At any point you can hardcode any of these and plug them directly into the class
#     MnM_rig_path=None
#     SHAPES_mel_paths=None
#     build_output_path=None
#     sdk_data_path=None

#     ### Dynamically build paths
#     char_dir = rf'{char_dir}{sep}{char_name}{sep}' # for example --- {C:\Users\harri\Documents\BDP\cha\}{jsh}{\}
#     output_filename=f'{char_name}_RIG_200_v{new_version:03}.ma' # for example --- {jsh}_RIG_200_v0{11}.ma
#     output_dir = rf'{char_dir}{output_dir_name}{sep}' # for example --- {C:\Users\harri\Documents\BDP\cha_input\jsh\}{output}{\}
#     SHAPES_dir = rf'{char_dir}{SHAPES_dir_name}{sep}' # for example --- {C:\Users\harri\Documents\BDP\cha_input\jsh\}{SHAPES}{\}
#     SHAPES_mel_paths=[]
#     for mel_file in SHAPES_mel_filenames:
#         SHAPES_mel_paths.append(f'{SHAPES_dir}{mel_file}') 
#     # for example --- ['C:\Users\harri\Documents\BDP\cha_input\jsh\SHAPES\}{M_jsh_base_body_geoShapes_blendShape.mel}',
#     #                  'C:\Users\harri\Documents\BDP\cha_input\jsh\SHAPES\}{M_jsh_base_cloth_top_fabric_geoShapes_blendShape.mel}']

#     ### Final filepath args: 
#     MnM_rig_path = rf'{char_dir}{MnM_build_file}'
#     SHAPES_mel_paths = SHAPES_mel_paths
#     build_output_path = f'{output_dir}{output_filename}' # for example --- '{C:\Users\harri\Documents\BDP\cha_input\jsh\output\}{jsh_RIG_200_v011.ma}'
#     sdk_data_path = rf'{char_dir}{sdk_filename}'

#     print(MnM_rig_path)
#     print(SHAPES_mel_paths)
#     print(build_output_path)
#     print(sdk_data_path)
