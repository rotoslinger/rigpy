import importlib
import os

def generate_dynamic_imports(file_paths, dynamic_imports):
    """
    Add dynamic import statements to specified files, removing any previous dynamic content.

    Args:
        file_paths (list): A list of file paths to update.
        dynamic_imports (str): The dynamic import code to insert.
    """
    for file_path in file_paths:
        # Read the existing content of the file
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # Remove any existing dynamic content
        new_lines = []
        in_dynamic_content = False
        
        for line in lines:
            if line.strip() == '# DYNAMIC GEN':
                in_dynamic_content = True
                new_lines.append(line)  # Keep the start marker
                continue
            elif line.strip() == '# DYNAMIC END':
                in_dynamic_content = False
                new_lines.append(line)  # Keep the end marker
                continue
            
            # Only add lines outside of the dynamic content block
            if not in_dynamic_content:
                new_lines.append(line)

        # Add the new dynamic imports at the top of the file
        new_lines.insert(0, dynamic_imports)

        # Write the modified content back to the file
        with open(file_path, 'w') as file:
            file.writelines(new_lines)


# Example usage
'''
from dynamic_importer import generate_dynamic_imports

# Specify the paths of the files you want to update
files_to_append = ['your_script1.py', 'your_script2.py']  # Add your file paths here

# Specify the dynamic import code
dynamic_import_code = """# DYNAMIC GEN
import importlib
import rigbdp.builders
importlib.reload(rigbdp.builders)
from rigbdp.builders import *
# DYNAMIC END
"""

# Call the function to add dynamic imports
generate_dynamic_imports(files_to_append, dynamic_import_code)
'''

# The three lines of imports below will dynamically get all shared imports.

# It is important to know these imports can be found here:
# rigpy/libs/rigbdp/builders/__init__.py

# This allows us to keep all common imports in a single file, and not have
# to hand edit a large amount of files every time we want to add something new.
