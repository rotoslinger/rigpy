import maya.cmds as cmds
import os, json
import glob


import maya.cmds as cmds
import os
import json

def ui_state_decorator(func):
    """
    Decorator that saves and restores UI state.
    It saves the state of the UI elements into a JSON file in Maya's local user prefs.
    """
    def wrapper(*args, **kwargs):
        # Get the UI name from the arguments or the function name
        ui_name = kwargs.get("ui_name", "default_ui")  # Can be passed via kwargs
        
        prefs_dir = cmds.internalVar(userPrefDir=True)
        prefs_file = os.path.join(prefs_dir, f"{ui_name}_state.json")

        # Load state if the file exists
        if os.path.exists(prefs_file):
            try:
                with open(prefs_file, 'r') as f:
                    state = json.load(f)
                    cmds.evalDeferred(lambda: restore_ui_state(state, ui_name))  # Restore after the UI is loaded
            except Exception as e:
                print(f"Error loading UI state: {e}")

        # Call the original function (creating the UI)
        func(*args, **kwargs)

        # Register a callback to save the UI state when the window is closed
        def on_close(*args):
            state = capture_ui_state()
            try:
                with open(prefs_file, 'w') as f:
                    json.dump(state, f, indent=4)
                print(f"UI state saved to {prefs_file}")
            except Exception as e:
                print(f"Error saving UI state: {e}")

        # Attach the close event handler
        if cmds.window(ui_name, exists=True):
            cmds.window(ui_name, e=True, closeCommand=on_close)

    return wrapper


def capture_ui_state():
    """
    Captures the state of the UI elements manually.
    This function can be extended to capture different UI widgets (e.g., sliders, checkboxes).
    """
    ui_state = {}

    # Capture state of specific UI elements (e.g., text fields, checkboxes)
    text_fields = ["charNameField"]  # Specify text field names you want to track
    for field in text_fields:
        if cmds.textField(field, exists=True):
            ui_state[field] = cmds.textField(field, q=True, text=True)

    checkboxes = ["rememberMe"]  # Specify checkbox names you want to track
    for box in checkboxes:
        if cmds.checkBox(box, exists=True):
            ui_state[box] = cmds.checkBox(box, q=True, value=True)

    return ui_state


def restore_ui_state(state, ui_name):
    """
    Restores the UI state from the given dictionary.
    """
    # Wait until the UI is fully initialized
    if not cmds.window(ui_name, exists=True):
        print(f"UI {ui_name} not found!")
        return

    for widget, value in state.items():
        if cmds.textField(widget, exists=True):
            cmds.textField(widget, e=True, text=value)
        elif cmds.checkBox(widget, exists=True):
            cmds.checkBox(widget, e=True, value=value)
        else:
            print(f"Unknown widget type for {widget}")

    print("UI state restored.")


@ui_state_decorator
def create_ui(ui_name="default_ui"):
    """
    Example UI creation function using the decorator.
    """
    if cmds.window(ui_name, exists=True):
        cmds.deleteUI(ui_name)

    window = cmds.window(ui_name, title="UI with State Saving")
    cmds.columnLayout(adjustableColumn=True)

    # Text Field
    cmds.textField("charNameField", placeholderText="Enter character name", width=300)

    # Checkbox
    cmds.checkBox("rememberMe", label="Remember me", value=False)

    # Button
    cmds.button(label="Save", command=lambda x: print("Saving UI state"))

    cmds.showWindow(window)



def create_char_structure(char_dir, char_name):
    """
    Creates the necessary directory structure for the character, but does not create any files.

    Args:
        char_dir (str): The base directory where the character structure should be created.
        char_name (str): The character name, which will create subdirectories for that character.

    Returns:
        dict: Dictionary with paths of created directories for the character.
    """
    sep = os.path.sep
    
    # Construct base paths
    char_base_dir = rf'{char_dir}{sep}{char_name}{sep}'  # For example: C:\Users\harri\Documents\BDP\build_demo\jsh\
    SHAPES_dir = rf'{char_base_dir}SHAPES{sep}'  # SHAPES directory for storing MEL files
    output_dir = rf'{char_base_dir}output{sep}'  # Output directory for output files
    input_dir = rf'{char_base_dir}input{sep}'  # Output directory for output files
    
    # Create the directories if they don't already exist
    os.makedirs(char_base_dir, exist_ok=True)  # Create the character base directory
    os.makedirs(SHAPES_dir, exist_ok=True)     # Create SHAPES directory
    os.makedirs(output_dir, exist_ok=True)     # Create output directory
    os.makedirs(input_dir, exist_ok=True)     # Create output directory

    # Return a dictionary with the paths of the created directories
    return {
        'char_base_dir': char_base_dir,
        'SHAPES_dir': SHAPES_dir,
        'output_dir': output_dir,
        'input_dir': input_dir
    }

def find_files(char_dir, char_name, new_version,
               MnM_extension='.ma', SHAPES_extension='.mel', sdk_filename='sdk_data.json'):
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
    
    # Constructing the dynamic character directory and other subdirectories
    char_dir = rf'{char_dir}{sep}{char_name}{sep}'
    SHAPES_dir = rf'{char_dir}SHAPES{sep}'
    output_dir = rf'{char_dir}output{sep}'
    input_dir = rf'{char_dir}input{sep}'
    
    # Find all files with the specified MnM and SHAPES extensions in their directories
    MnM_rig_path = glob.glob(f'{input_dir}*{MnM_extension}')
    SHAPES_mel_paths = glob.glob(f'{SHAPES_dir}*{SHAPES_extension}')
    
    # Construct output filename based on character name and version
    output_filename = f'{char_name}_RIG_200_v{new_version:03}.ma'
    build_output_path = f'{output_dir}{output_filename}'

    # Path for sdk data file
    sdk_data_path = rf'{input_dir}{sdk_filename}'
    
    # Return a dictionary with all found file paths
    return {
        'MnM_rig_path': MnM_rig_path[0] if MnM_rig_path else None,
        'SHAPES_mel_paths': SHAPES_mel_paths,
        'build_output_path': build_output_path,
        'sdk_data_path': sdk_data_path
    }

@ui_state_decorator
def create_directory_ui():
    """
    UI to allow the user to input a character name, directory path and create the directory structure.
    """
    def on_create_structure(*args):
        # Get user inputs
        char_name = cmds.textField('charNameField', q=True, text=True)
        char_dir = cmds.textField('dirPathField', q=True, text=True)
        
        # Ensure the base directory exists
        if not os.path.exists(char_dir):
            cmds.confirmDialog(title="Error", message="Base directory does not exist.", button=["OK"])
            return
        
        created_dirs = create_char_structure(char_dir, char_name)
        
        # Print out the dictionary with created directories
        print("Created Directory Structure:")
        print(created_dirs)
        
        # Show confirmation with paths
        cmds.confirmDialog(title="Directories Created", message=str(created_dirs), button=["OK"])
    
    window_name = 'createDirWindow'

    # If window already exists, delete it
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)

    # Create window
    cmds.window(window_name, title="Create Directory Structure")
    cmds.columnLayout(adjustableColumn=True)

    # Character Name input
    cmds.text(label="Character Name:")
    cmds.textField('charNameField', placeholderText="Enter character name", width=300)

    # Directory Path input
    cmds.text(label="Directory Path:")
    cmds.textField('dirPathField', placeholderText="Enter base directory path", width=300)

    # Button to select the directory using file dialog
    cmds.button(label="Select Directory", command=lambda x: select_directory('dirPathField'))

    # Create Directory Structure button
    cmds.button(label="Create Directory Structure", command=on_create_structure)

    # Spacer
    cmds.separator(height=10)

    # Button to construct file paths
    cmds.button(label="Construct File Paths", command=on_construct_file_paths)

    cmds.showWindow(window_name)

def select_directory(text_field_name):
    """
    Opens a file dialog for the user to select a directory and sets it in the text field.
    """
    directory = cmds.fileDialog2(fileMode=3, okCaption="Select Directory")
    if directory:
        cmds.textField(text_field_name, e=True, text=directory[0])

def on_construct_file_paths(*args):
    """
    Calls the find_files function and prints out the dictionary of file paths.
    """
    char_name = cmds.textField('charNameField', q=True, text=True)
    char_dir = cmds.textField('dirPathField', q=True, text=True)
    new_version = 11  # This can be dynamically set via another text field or input.
    
    file_paths = find_files(char_dir, char_name, new_version)
    
    # Print the resulting file paths
    print("Constructed File Paths:")
    print(file_paths)
    
    # Show confirmation with paths
    cmds.confirmDialog(title="File Paths Constructed", message=str(file_paths), button=["OK"])

# Launch the UI
create_directory_ui()
