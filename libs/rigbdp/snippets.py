from functools import wraps
from maya import cmds

OTHER = ['M_freeze_env', 'spaces_grp', 'modules_grp', 'rigGeo_ndStep_grp', 'rigGeo_200_grp']


def suppress_warnings(func):
    # suppress_warnings, but only while the function runs. Func is safe to fail.  Do not use with quit() or sys.exit()!
    @wraps(func)
    def wrapper(*args, **kwargs):
        cmds.scriptEditorInfo(suppressWarnings=True)
        result = func(*args, **kwargs)
        cmds.scriptEditorInfo(suppressWarnings=False)
        return result
    return wrapper

@suppress_warnings
def setup_rig_vis(channel_box = True, hidden_in_outliner=False, skin_jnt_vis=False, sculpt_jnt_vis=True):
    # create divider
    if not cmds.objExists('preferences.__________________'):
        cmds.addAttr('preferences', longName="__________________", attributeType='enum', enumName='_________:')
        cmds.setAttr('preferences.__________________', e=True, channelBox=True)

    long_names=['rig_hidden_in_outliner', 'skin_joints_vis', 'sculpt_joints_vis']
    nice_names=['Rig Hidden In Outliner', 'Skin Joints Visibility', 'Sculpt Joints Visibility']

    for index, attr in enumerate(long_names):
        if not cmds.objExists(f'preferences.{attr}'):
            cmds.addAttr('preferences', longName=long_names[index], niceName=nice_names[index], attributeType='bool')
        cmds.setAttr(f'preferences.{attr}', e=True, channelBox=True)

    hidden_in_outliner_attr = 'preferences.rig_hidden_in_outliner'
    skin_vis_attr = 'preferences.skin_joints_vis'
    sculpt_vis_attr = 'preferences.sculpt_joints_vis'
    full_attrs = [hidden_in_outliner_attr, skin_vis_attr, sculpt_vis_attr]

    rig_root = 'rig_grp'
    skin_grp = 'skel_grp'
    sculpt_jnts = 'M_masterWalkOut_jnt'
    all_objects = [rig_root, skin_grp, sculpt_jnts] + OTHER

    for obj in all_objects:
        cmds.connectAttr(hidden_in_outliner_attr, f'{obj}.hiddenInOutliner', force=True)
        cmds.setAttr(f'{obj}.v', e=True, lock=False, channelBox=channel_box, keyable=False)
        if 'skel' in obj:
            cmds.connectAttr(skin_vis_attr, f'{skin_grp}.v', force=True)
        if 'M_masterWalkOut_jnt' in obj:
            cmds.connectAttr(sculpt_vis_attr, f'{sculpt_jnts}.v', force=True)
    full_attrs.insert(0, 'preferences.__________________')

    # sets arg attr vals
    arg_attrs = [None, hidden_in_outliner, skin_jnt_vis, sculpt_jnt_vis]

    cmds.setAttr(f'{rig_root}.v', True)

    # whether to see in the channel box
    for index, name in enumerate(full_attrs):
        cmds.setAttr(name, e=True, channelBox=channel_box)
        if index > 0:
            cmds.setAttr(name, arg_attrs[index])
