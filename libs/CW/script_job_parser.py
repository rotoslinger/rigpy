# NOTE: call to create_script_job will be added dynamically when the script node is created
# BEGIN BEFORE SCRIPT ==============================================================================

import maya.cmds as cmds

def align_attr_changed(node, attribute, previous_attr):
    """Prints the value of the specified attribute for the given node and tracks changes."""
    if cmds.objExists(node):
        current_value = cmds.getAttr(attribute)
        previous_value = cmds.getAttr(previous_attr) if cmds.objExists(previous_attr) else None
        
        print(f'Attribute {attribute} change from {previous_value} to {current_value}')
        if previous_value is not None:
            print(f'Previous attribute {previous_attr} value: {previous_value}')

def create_script_job(node, attribute, previous_attr):
    """Creates a script job to monitor changes to the specified attribute of the given node."""
    attribute_full_name = f'{node}.{attribute}'
    previous_attr_full_name = f'{node}.{previous_attr}'  # Full name of the previous attribute
    option_var_readable = f'{node}_{attribute}'

    # A wrapper function to track attribute changes
    def wrapper():
        align_attr_changed(node, attribute_full_name, previous_attr_full_name)

        # After printing the values, update the previous attribute with the current value
        cmds.setAttr(previous_attr_full_name, cmds.getAttr(attribute_full_name))

    # Initialize the previous attribute value if it doesn't exist yet
    if not cmds.objExists(previous_attr_full_name):
        # Set the initial value for the previous attribute to match the current attribute
        initial_value = cmds.getAttr(attribute_full_name)
        cmds.setAttr(previous_attr_full_name, initial_value)

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
