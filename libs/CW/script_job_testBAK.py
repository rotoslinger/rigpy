import os

import maya.cmds as cmds

ALIGN_SCRIPT_NODE_CONTENT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "script_job_parser.py"
)

def align_attr_changed(node, attribute, previous_values):
    """Prints the value of the specified attribute for the given node and tracks changes."""
    if cmds.objExists(node):
        current_value = cmds.getAttr(attribute)
        previous_value = previous_values.get(attribute, current_value)
        print(f'Attribute {attribute} changed from {previous_value} to {current_value}')
        previous_values[attribute] = current_value  # Update the previous value


def get_script_node_content(file_path, node, attribute):
    before_script_content = []
    after_script_content = []
    current_section = None

    with open(file_path, "r") as f:
        for line in f:
            if line.startswith("# BEGIN BEFORE SCRIPT"):
                current_section = before_script_content
            elif line.startswith("# BEGIN AFTER SCRIPT"):
                current_section = after_script_content
            elif line.startswith("# END BEFORE SCRIPT") or line.startswith("# END AFTER SCRIPT"):
                current_section = None
            elif current_section is not None:
                current_section.append(line)

    before_script_content.append(f'create_script_job("{node}", "{attribute}")\n')
    after_script_content.append(f'delete_script_job("{node}", "{attribute}")\n')

    return "".join(before_script_content), "".join(after_script_content)


def create_script_node(node, attribute, create=True, delete=False):
    before_script, after_script = get_script_node_content(ALIGN_SCRIPT_NODE_CONTENT_PATH,
                                                          node=node, attribute=attribute)
    # make sure the script job does not exist
    exec(after_script)

    # Script to create the script job when the scene is opened
    open_script = before_script
    
    # Script to delete the script job when the scene is closed
    close_script = after_script
    script_node= 'attributeMonitorScriptNode'
    if cmds.objExists(script_node):
        cmds.delete(script_node)

    # Create the script node
    script_node = cmds.scriptNode(
        scriptType=2,  # Run on scene open/close
        beforeScript=open_script,
        afterScript=close_script,
        name='attributeMonitorScriptNode',
        sourceType='python'
    )
    print(before_script)
    if create:
        # Execute the open script directly to start monitoring immediately
        exec(before_script)
    if delete:
        exec(after_script)

def delete_script_node(node, attribute):
    after_script = get_script_node_content(ALIGN_SCRIPT_NODE_CONTENT_PATH,
                                           node=node, attribute=attribute)[1]
    # make sure the script job does not exist
    exec(after_script)
    script_node= 'attributeMonitorScriptNode'
    if cmds.objExists(script_node):
        cmds.delete(script_node)



# Run the function to create the script node
# create_script_node(node='pCube1', attribute='translateX')
