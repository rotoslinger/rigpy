
try:
    import maya.standalone

    maya.standalone.initialize()
except:
    pass

import maya.cmds as cmds
import os

ALIGN_SCRIPT_NODE_CONTENT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "maya_align_script_node.py")

# new_node_names the name of new nodes to be added 
# parent_func_attrs where to parent the controls class/func instance attrs 

def space_switcher(ctrl,
                   make_names: list | None = None, # list of names to create xforms for
                   make_parents: list | None = None, # where to parent the new xforms 
                   space_dict: dict = {'World':'world_null',
                                       'Chest':'Spine2',
                                       }):
    '''
    creates new transforms for spaces and a space switch attribute for the specified control
    '''
    enum_list = space_dict.keys()
    enum_str = ':'.join(enum_list)

    if not cmds.objExists(f'{ctrl}.align'):
        cmds.addAttr(ctrl, longName='align', attributeType='enum',
                     enumName=enum_str, keyable=True)

    if make_names and make_parents:
        for name, parent in zip(make_names, make_parents):
            new_node = cmds.createNode('transform', name=name, parent=parent)
            ws_matrix = cmds.xform(parent, matrix=True, ws=True)