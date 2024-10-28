import os, sys, platform

from arpdecorator import asciiart


# The Maya.env file is located in C:\Users\<Username>\Documents\maya\<version_number>\ on Windows,
# $HOME/maya/<version_number>/ on Linux,
# and $HOME/Library/Preferences/Autodesk/maya/<version_number>/ on macOS.



def update_maya_env(env_path, debug=False):
    # Ensure the file path is properly formatted for the current OS

    # Find the path of the currently running script
    module_path = os.path.dirname(os.path.realpath(__file__))

    # Construct the path to the Maya.env file
    env_file = os.path.join(env_path, "Maya.env")
    module_path = os.path.normpath(module_path)

    if debug:
        print(f"Debug Mode: ON")
        print(f"Drag Drop Install path to copy: {module_path}")
        print(f"Maya.env location: {env_file}")

    # Check if the Maya.env file exists; if not, create it
    if not os.path.exists(env_file):
        if debug:
            print("Maya.env does not exist. Creating a new file.")
        # Create the Maya.env file and add a default PYTHONPATH entry
        with open(env_file, 'w') as f:
            f.write("PYTHONPATH=\n")  # Initialize with an empty PYTHONPATH
        if debug:
            print(f"Created {env_file} with default content.")

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

def update_python_path(maya_year):
    platform_info = platform.system()
    home_dir = os.path.expanduser("~")
    try:
        print(f'updating the maya.env at : {home_dir}/maya/{maya_year}')
        if platform_info == 'Linux':
            update_maya_env(f'{home_dir}/maya/{maya_year}', debug=False)
        elif platform_info == 'Darwin':
            update_maya_env(f'{home_dir}/Library/Preferences/Autodesk/maya/{maya_year}')
        elif platform_info == 'Windows':
            update_maya_env(rf'{home_dir}\Documents\maya\{maya_year}', debug=False)
        else:
            print("You are now entering the twilight zone")
        print(f"Installed for Maya {maya_year}.")
        return True
    except:
        return False


MAYA_YEAR = [2020, 2021, 2022, 2023, 2024, 2025]

@asciiart.draw_random_art
def update_maya():
    success = []
    for year in MAYA_YEAR:
        success.append(update_python_path(str(year)))
    if sum(success) > 0:
        print('PYTHONPATH updated in Maya.env successfully.')
update_maya()