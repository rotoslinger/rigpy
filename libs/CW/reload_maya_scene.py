from importlib import reload
from maya import mel, cmds

from CW import maya_weights
from CW import maya_align_ctrl

reload(maya_weights)

def load_maya_scene():
    mel.eval('file -f -options "v=0;"  -ignoreVersion  -typ "mayaAscii" -o "C:/Users/harri/Documents/cartwheel/working_files/mani.ma";addRecentFile("C:/Users/harri/Documents/cartwheel/working_files/mani.ma", "mayaAscii");')

def main():
    cmds.setAttr('right_elbow_fk_ctrl.rx', 0)
    cmds.setAttr('right_elbow_fk_ctrl.ry', 0)
    cmds.setAttr('right_elbow_fk_ctrl.rz', 0)

    twist_weights = maya_weights.Weights()

    up_arm_jnts = ['RightArm_out_bind_tw01', 'RightArm_out_bind_tw02', 'RightArm_out_bind_tw03', 'RightArm_out_bind_tw04', 'RightArm_out_bind_tw05',  'RightArm_out_bind_tw06', ]
    lo_arm_jnts = ['RightForeArm_out_bind_tw01', 'RightForeArm_out_bind_tw02', 'RightForeArm_out_bind_tw03', 'RightForeArm_out_bind_tw04', 'RightForeArm_out_bind_tw05', 'RightForeArm_out_bind_tw06',]
    maya_align_ctrl.create_space_switch_attrs(control='left_elbow_fk_ctrl',
                                              align=True,
                                              position=False,
                                              full=False,
                                              space_joints={'world_null':'World', 'Spine2':'Chest',}
                                              )
    # twist_weights.distribute_twist_weights(start_joint='RightArm',
    #                                        end_joint='RightForeArm',
    #                                        twist_joints=up_arm_jnts)

    # twist_weights.distribute_twist_weights(start_joint='RightForeArm',
    #                                        end_joint='RightHand',
    #                                        twist_joints=lo_arm_jnts)
    # twist_weights.select_points_between_startend('Body_geo',
    #                                              'RightForeArm_out_bind_tw05',
    #                                              'RightForeArm_out_bind_tw06')
    # print(twist_weights.list_methods())
load_maya_scene()
main()
