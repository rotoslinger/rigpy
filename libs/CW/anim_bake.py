
import maya.cmds as cmds

r'''
1. on each frame locators would be placed for fk wrist, elbow (and leg equivalents)
2. the ik wrist and elbow would be snapped to the fk wrist, elbow to get a clean Ry animation.
3. snap locators to the joints LeftArm, LeftForeArm, LeftHand per frame.
4. bake those rotations back into the fk control animation
5. garbage collection (delete locators etc.)

'''
import maya.cmds as cmds

def clean_up_axis(fk_ctrls,
                  switch='',
                  ik_ctrls='',
                  bone_names='',
                  debug=True):
    start_frame = cmds.playbackOptions(query=True, minTime=True)
    end_frame = cmds.playbackOptions(query=True, maxTime=True)

    for index, ctrl in enumerate(fk_ctrls):
        if index == 0: continue
        tmp_node = cmds.createNode('transform', name=f'{ctrl}_tmpxform')
        # Uneeded, for UI debug testing
        if debug: cmds.createNode('locator',
                                  name=f'{ctrl}_tmpShape',
                                  parent=tmp_node)
        tmp_cons = cmds.pointConstraint(ctrl,
                                        tmp_node,
                                        maintainOffset=False)
        cmds.bakeResults(
            tmp_node,
            simulation=False,
            time=(start_frame, end_frame),
            sampleBy=1,
            oversamplingRate=1,
            disableImplicitControl=True,
            preserveOutsideKeys=True,
            sparseAnimCurveBake=False,
            removeBakedAttributeFromLayer=False,
            removeBakedAnimFromLayer=False,
            bakeOnOverrideLayer=False,
            minimizeRotation=True,
            controlPoints=False,
            shape=False
        )
        cmds.delete(tmp_cons)

fk_ctrls=['left_shoulder_fk_ctrl', 'left_elbow_fk_ctrl', 'left_wrist_fk_ctrl']
ik_ctrls = ['left_elbow_ik_ctrl', 'left_wrist_ik_ctrl']
switch = 'left_hand_ctrl'
clean_up_axis(fk_ctrls=fk_ctrls, ik_ctrls=ik_ctrls)

# You may need to find the arm, elbow, hand order procedurally, if so, write:
def sort_ctrls(ctrls, forward_vector, part_hint='arm'):
    '''
    sorts a list of transforms based on their forward vector position
    part hint could be arm or leg. Depends on naming convention.
    '''
    