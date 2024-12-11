# NOTE: call to create_script_job will be added dynamically when the script node is created
# BEGIN BEFORE SCRIPT ==============================================================================

import maya.cmds as cmds

def align_attr_changed(node, attribute, previous_values):
    """Prints the value of the specified attribute for the given node and tracks changes."""
    if cmds.objExists(node):
        current_value = cmds.getAttr(attribute)
        previous_value = previous_values.get(attribute, current_value)
        print(f'Attribute {attribute} changed from {previous_value} to {current_value}')
        previous_values[attribute] = current_value  # Update the previous value

def create_script_job(node, attribute):
    """Creates a script job to monitor changes to the specified attribute of the given node."""
    attribute_full_name = f'{node}.{attribute}'
    option_var_readable = f'{node}_{attribute}'

    # Store previous values in a dictionary to avoid global variables
    previous_values = {}

    # A wrapper function to track attribute changes
    def wrapper():
        align_attr_changed(node, attribute_full_name, previous_values)

    # Create a dynamic script job ID based on object and attribute
    job_id = cmds.scriptJob(attributeChange=[attribute_full_name, wrapper])

    # Create a human-readable version of the job ID
    cmds.optionVar(intValue=(option_var_readable, job_id))

# END BEFORE SCRIPT ================================================================================

# NOTE: call to delete_script_job will be added dynamically when this script is retrieved
# BEGIN AFTER SCRIPT ===============================================================================

import maya.cmds as cmds

def delete_script_job(node, attribute):
    option_var_readable = f'{node}_{attribute}'

    if cmds.optionVar(exists=option_var_readable):
        job_id = cmds.optionVar(query=option_var_readable)
        if cmds.scriptJob(exists=job_id):
            cmds.scriptJob(kill=job_id, force=True)
        cmds.optionVar(remove=option_var_readable)

# END AFTER SCRIPT =================================================================================
