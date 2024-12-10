
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

def create_space_switch(ctrl,
                        make_names: list | None = None, # list of names to create xforms for
                        make_parents: list | None = None, # where to parent the new xforms 
                        space_dict: dict = {'World':'world_null',
                                            'Chest':'Spine2'},
                        follow=False
                        ):
    '''
    creates new transforms for spaces and a space switch attribute for the specified control
    '''

    if follow:
        # NOTE: where you store the rot/pos of the control before the switch happens.
        add_storage_attrs(ctrl, attr_name='cur_rotate')
        add_storage_attrs(ctrl, attr_name='cur_translate')
        if not cmds.objExists(f'{ctrl}.FOLLOW'):
            cmds.addAttr(ctrl, longName='FOLLOW', attributeType='bool',
                            keyable=False, hidden=True)

    enum_list = space_dict.keys()
    enum_str = ':'.join(enum_list)

    if not cmds.objExists(f'{ctrl}.align'):
        cmds.addAttr(ctrl, longName='align', attributeType='enum',
                     enumName=enum_str, keyable=True)
        
    # NOTE: may not be needed...    
    if not cmds.objExists(f'{ctrl}.align_cur_state'):
        cmds.addAttr(ctrl, longName='align_cur_state', attributeType='enum',
                     enumName=enum_str, keyable=False, hidden=True)
    
    # NOTE: where you store the position of the control before the switch happens.
    if not cmds.objExists(f'{ctrl}.ctrl_cur_matrix'):
        cmds.addAttr(ctrl, ln='ctrl_cur_matrix', at='matrix', keyable=False, hidden=True)

    if make_names and make_parents:
        for name, parent in zip(make_names, make_parents):
            new_node = cmds.createNode('transform', name=name, parent=parent)
            ws_matrix = cmds.xform(parent, matrix=True, ws=True, query=True)
            cmds.xform(new_node, matrix=ws_matrix, ws=True)
            [cmds.setAttr(f'{new_node}.{attr}{axis}',
                          lock=True) for attr in ('translate', 'rotate', 'scale') for axis in 'XYZ']
            if 'world' in name:
                cmds.setAttr(f'{new_node}.inheritsTransform', 0)

    constraints = cmds.listConnections(ctrl, type="constraint", source=True, destination=False)


def add_storage_attrs(ctrl, attr_name='cur_rotate'):
    """
    Adds a compound attribute to store attributes used for compensation
    cur_rotate_x, cur_rotate_y, cur_rotate_z or cur_translate_x, cur_translate_y, cur_translate_z
    """
    if cmds.objExists(f'{ctrl}.{attr_name}'):
        if not cmds.about(batch=True):
            print(f'Attribute "{attr_name}" already exists on "{ctrl}".')
        return
    
    # Add the compound attribute for rotations
    cmds.addAttr(ctrl, ln=attr_name, at='compound', numberOfChildren=3, keyable=False, hidden=True)
    cmds.addAttr(ctrl, ln=f'{attr_name}_x', at='double', parent=attr_name,
                 keyable=False, hidden=True)
    cmds.addAttr(ctrl, ln=f'{attr_name}_y', at='double', parent=attr_name,
                 keyable=False, hidden=True)
    cmds.addAttr(ctrl, ln=f'{attr_name}_z', at='double', parent=attr_name,
                 keyable=False, hidden=True)

    return f'{ctrl}.{attr_name}', f'{attr_name}_x', f'{attr_name}_y', f'{attr_name}_z'
    
def buffer_in_place(maya_obj, new_buffer_name):
    """Parent maya object to new transform at the same world position and hier location."""
    parent = cmds.listRelatives(maya_obj, parent=True)
    buffer = cmds.createNode('transform', parent=parent, name=new_buffer_name)
    cmds.matchTransform(buffer, maya_obj)
    cmds.parent(maya_obj, buffer)
    return buffer
