from maya import cmds

# get the world space matrix of the control before the align switch
# set it in a hidden attribute

# do the switch

# retrieve the hidden attribute
# set the hidden attribute on the control.

# BEGIN BEFORE SCRIPT ==========================================================
import maya.cmds as cmds

def align_attr_changed(node, attribute):
    """Prints the value of the specified attribute for the given node."""
    if cmds.objExists(node):
        value = cmds.getAttr(attribute)
        print(f'Attribute {attribute} changed: {value}')

def create_script_job(node, attribute):
    """Creates a script job to monitor changes to the specified attribute of the given node."""
    attribute_full_name = f'{node}.{attribute}'
    option_var_readable = f'{node}_{attribute}'

    # A hacky way to pass in args...
    def wrapper():
        align_attr_changed(node, attribute_full_name)

    # Create a dynamic script job ID based on object and attribute
    job_id = cmds.scriptJob(attributeChange=[attribute_full_name, wrapper])

    # create a human readable version of the job id
    cmds.optionVar(intValue=(option_var_readable, job_id))

# END BEFORE SCRIPT =============================================================

# BEGIN AFTER SCRIPT ==========================================================
import maya.cmds as cmds

def delete_script_job(node, attribute):
    option_var_readable = f'{node}_{attribute}'

    if cmds.optionVar(exists=option_var_readable):
        job_id = cmds.optionVar(query=option_var_readable)
        if cmds.scriptJob(exists=job_id):
            cmds.scriptJob(kill=job_id, force=True)
        cmds.optionVar(remove=option_var_readable)

# END AFTER SCRIPT =============================================================
'''
# BEGIN BEFORE SCRIPT ==========================================================
import maya.cmds as cmds

def print_attribute_value(node, attribute):
    """Prints the value of the specified attribute for the given node."""
    if cmds.objExists(node):
        value = cmds.getAttr(attribute)
        print(f'Attribute {attribute} changed: {value}')

def create_script_job(node, attribute):
    """Creates a script job to monitor changes to the specified attribute of the given node."""
    attribute_full_name = f'{node}.{attribute}'
    option_var_readable = f'{node}_{attribute}'

    # A hacky way to pass in args...
    def wrapper():
        print_attribute_value(node, attribute_full_name)

    # Create a dynamic script job ID based on object and attribute
    job_id = cmds.scriptJob(attributeChange=[attribute_full_name, wrapper])

    # create a human readable version of the job id
    cmds.optionVar(intValue=(option_var_readable, job_id))

# END BEFORE SCRIPT =============================================================

# BEGIN AFTER SCRIPT ==========================================================
import maya.cmds as cmds

def delete_script_job(node, attribute):
    option_var_readable = f'{node}_{attribute}'

    if cmds.optionVar(exists=option_var_readable):
        job_id = cmds.optionVar(query=option_var_readable)
        if cmds.scriptJob(exists=job_id):
            cmds.scriptJob(kill=job_id, force=True)
        cmds.optionVar(remove=option_var_readable)

# END AFTER SCRIPT =============================================================





'''