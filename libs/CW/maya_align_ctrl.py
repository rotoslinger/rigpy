
try:
    import maya.standalone

    maya.standalone.initialize()
except:
    pass

import maya.cmds as cmds
import os

ALIGN_SCRIPT_NODE_CONTENT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "maya_fkik_script_node.py")

def create_space_switch_attrs(control,
                              align=True,
                              position=False,
                              full=False,
                              space_joints={'world_null':'World', 'Spine2':'Chest',}):
    '''
    creates attrs on the specified control for align, position, and parent(full)
    '''
    