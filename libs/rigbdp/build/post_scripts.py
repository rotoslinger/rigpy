from maya import cmds
#create and place M_spineUpperChestOut_jnt
def create_upchest_sculpt_jnt():
    cmds.select( d=True )
    cmds.joint('M_spineChestOut_jnt', n='M_spineUpperChestOut_jnt', p=(0, 0, 0) )
    cmds.parentConstraint('M_spineUpperChestGimbal_ctrl', 'M_spineUpperChestOut_jnt')
    #cmds.scaleConstraint('M_spineUpperChestGimbal_ctrl', 'M_spineUpperChestOut_jnt')#might be ok to leave scales while working since they shouldn't be effected

    #temporarily remove constraints to reparent immediate children of M_spineUpperChestOut_jnt

    cmds.delete('L_clavicleOut_JNT_parentConstraint')
    cmds.delete('R_clavicleOut_JNT_parentConstraint')

    cmds.delete('M_neckHead00Out_JNT_parentConstraint')

    #reparent new joints

    cmds.parent('L_clavicleOut_jnt', 'R_clavicleOut_jnt', 'M_neckHead00Out_jnt', 'M_spineUpperChestOut_jnt')

    #re-constrain joints to original drivers

    cmds.parentConstraint("L_clavicle_ctrl", "L_clavicleOut_jnt", mo=True)
    cmds.parentConstraint("R_clavicle_ctrl", "R_clavicleOut_jnt", mo=True)
    cmds.parentConstraint("M_neckHead00_env", "M_neckHead00Out_jnt", mo=True)

    cmds.rename('L_clavicleOut_jnt_parentConstraint1', 'L_clavicleOut_JNT_parentConstraint')
    cmds.rename('R_clavicleOut_jnt_parentConstraint1', 'R_clavicleOut_JNT_parentConstraint')
    cmds.rename('M_spineUpperChestOut_jnt_parentConstraint1', 'M_neckHead00Out_JNT_parentConstraint')
