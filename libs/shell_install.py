import os
import sys

def update_maya_env(env_path, debug=False):
    # Ensure the file path is properly formatted for the current OS

    # Find the path of the currently running script
    module_path = os.path.dirname(os.path.realpath(__file__))

    # Ensure the file path is properly formatted for the current OS
    env_file = f'{env_path}{os.path.sep}Maya.env'
    module_path = os.path.normpath(module_path)

    if debug:
        print(f"Debug Mode: ON")
        print(f"Drag Drop Install path to copy: {module_path}")
        print(f"Maya.env location: {env_file}")

    # Check if the Maya.env file exists
    if not os.path.exists(env_file):
        if debug:
            print("Maya.env does not exist yet.")
        return

    # Read the current contents of Maya.env
    with open(env_file, 'r') as f:
        env_content = f.readlines()

    # Find the current PYTHONPATH in the Maya.env file
    pythonpath_line = next((line for line in env_content if line.startswith("PYTHONPATH=")), None)

    # Get current paths, or initialize an empty list if PYTHONPATH is not found
    if pythonpath_line:
        current_paths = pythonpath_line.strip().split('=')[1].split(';')

        # Remove any empty strings caused by trailing semicolons
        current_paths = [p for p in current_paths if p]

    else:
        current_paths = []

    if debug:
        print(f"Current PYTHONPATH: {pythonpath_line}")
        print(f"Current paths list: {current_paths}")

    # Check if the module_path is already in PYTHONPATH
    if module_path not in current_paths:
        current_paths.append(module_path)

    # Prepare the new PYTHONPATH entry
    new_pythonpath = "PYTHONPATH=" + ';'.join(os.path.normpath(p) for p in current_paths)

    if debug:
        print(f"PYTHONPATH after modification: {new_pythonpath}")
        print(f"New Maya.env would look like:\n{new_pythonpath}")
    
    # If not in debug mode, write the changes to Maya.env
    if not debug:
        with open(env_file, 'w') as f:
            # Write back all non-PYTHONPATH lines first
            for line in env_content:
                if not line.startswith("PYTHONPATH="):
                    f.write(line)
            # Write the updated PYTHONPATH at the end
            f.write(new_pythonpath + "\n")
        print(f"PYTHONPATH updated in Maya.env successfully.")
update_maya_env(r'C:\Users\harri\Documents\maya\2024', debug=False)