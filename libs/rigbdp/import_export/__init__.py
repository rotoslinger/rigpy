import os

from maya import cmds


# Get the full path of the current scene
def get_scene_dir():
    current_scene = cmds.file(q=True, sn=True)
    # make sure the scene exists somewhere (you need to save to a directory to find out where the file is saved)
    if current_scene:
        # Extract the directory from the full scene path
        return os.path.dirname(current_scene)
    else:
        print("No saved scene is open. Save first, then try again")
        return None




def export_to_json(data, file_path=None, filename_prefix='',  suffix="MATRIX_CONNECTIONS"):
    """
    Exports a dictionary to a JSON file using the node name and a custom file path.
    Args:
    - data (dict): The dictionary to export.
    - node (str): The node name to use in the JSON file name.
    - file_path (str): The file path where the JSON file will be saved.
    - suffix (str): The suffix to append to the filename.
    """
    # Create the full file name using the node name and suffix
    if not file_path:
        file_path = get_scene_dir()
    file_name = f"{filename_prefix}_{suffix}.json"
    full_file_path = os.path.join(file_path, file_name)

    # Export the dictionary to a JSON file
    with open(full_file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    print("\n")
    print(f"Exported to {full_file_path}")
    print("\n")

#################################### Usage ####################################
# scene_dir = get_scene_dir()
# print("The current scene has been saved here: " + scene_dir)
###############################################################################