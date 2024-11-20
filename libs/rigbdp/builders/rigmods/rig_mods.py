import maya.cmds as cmds
import maya.OpenMaya as om

#import pymel.core as pm
import math

def create_lips_sculpt_jnts():
    sides = ['L_','R_']
    for side in sides:
        cmds.select(cl=True)
        cmds.select(side + 'lips_offset')
        cmds.joint(n=side + 'lips_jntPSD', )

        cmds.parentConstraint(side + 'lips_ctrl', side + 'lips_jntPSD', mo=False)

def connect_common_blendshapes(char_name='jsh'):
    blendShapeWeight_Body = cmds.listAttr(f'M_{char_name}_base_body_geoShapes_blendShape.w', m=True)
    blendShapeWeight_clothes = cmds.listAttr(f'M_{char_name}_base_cloth_top_fabric_low_geoShapes_blendShape.w', m=True)

    common_targets = list(set(blendShapeWeight_Body) & set(blendShapeWeight_clothes))

    for common_target in common_targets:
        cmds.connectAttr(f'M_{char_name}_base_body_geoShapes_blendShape.' + common_target, f'M_{char_name}_base_cloth_top_fabric_low_geoShapes_blendShape.' + common_target)

def BDP_outSkel_rigMod():
    
    ##########################################################################################
    '''
    M_lipsMuzzle_ctrl
    
    '''
    ##########################################################################################
    #create and place M_spineUpperChestOut_jnt

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
    
    ############
    #create new IK/FK out skeleton joints
    ############
    
    sides = ['L_', 'R_']
    
    for side in sides:
        
        cmds.duplicate(side + 'arm00Out_jnt', rc=True)
        jnts = cmds.listRelatives(side + 'arm00Out_jnt1', ad=True)

        for jnt in jnts:
            
            if jnt == side + 'arm00Out_jnt1':
               pass
            
            elif jnt == side + 'arm05Out_jnt1':
               pass
            elif jnt == side + 'hand00Out_jnt1':
               pass
                   
            else:
                cmds.delete(jnt)
                
        cmds.rename(side + 'arm00Out_jnt1', side + 'armUpOut_jntNull')
        cmds.rename(side + 'arm05Out_jnt1', side + 'armLowOut_jntNull')
        cmds.rename(side + 'hand00Out_jnt1', side + 'handOut_jntNull')

        # point constraint/delete to inherit location (maintain offset off)
        con1 = cmds.pointConstraint(side + 'fkArmMechanics00_jnt', side + 'ikArmIKMechanics00_jnt', side + 'armUpOut_jntNull', mo=False)
        con2 = cmds.pointConstraint(side + 'fkArmMechanics01_jnt', side + 'ikArmIKMechanics01_jnt', side + 'armLowOut_jntNull', mo=False)
        con3 = cmds.pointConstraint(side + 'fkArmMechanics02_jnt', side + 'ikArmIKMechanics02_jnt', side + 'handOut_jntNull', mo=False)
        cmds.delete(con1, con2, con3)

        # parent constrain with maintain offset on
        cmds.parentConstraint(side + 'fkArmMechanics00_jnt', side + 'ikArmIKMechanics00_jnt', side + 'armUpOut_jntNull', mo=True)
        cmds.parentConstraint(side + 'fkArmMechanics01_jnt', side + 'ikArmIKMechanics01_jnt', side + 'armLowOut_jntNull', mo=True)
        cmds.parentConstraint(side + 'fkArmMechanics02_jnt', side + 'ikArmIKMechanics02_jnt', side + 'handOut_jntNull', mo=True)

        #connect FK/IK blends

        #up
        cmds.shadingNode('reverse', asUtility=True, n=side + 'armUpOut_jntNull_reverse')

        cmds.connectAttr(side + 'armSettings_ctrl.fkIkBlend', side + 'armUpOut_jntNull_reverse.inputX')
        cmds.connectAttr(side + 'armUpOut_jntNull_reverse.outputX', side + 'armUpOut_jntNull_parentConstraint1.' + side + 'ikArmIKMechanics00_jntW1')
        cmds.connectAttr(side + 'armSettings_ctrl.fkIkBlend', side + 'armUpOut_jntNull_parentConstraint1.' + side + 'fkArmMechanics00_jntW0')

        #low
        cmds.shadingNode('reverse', asUtility=True, n=side + 'armLowOut_jntNull_reverse')

        cmds.connectAttr(side + 'armSettings_ctrl.fkIkBlend', side + 'armLowOut_jntNull_reverse.inputX')
        cmds.connectAttr(side + 'armLowOut_jntNull_reverse.outputX', side + 'armLowOut_jntNull_parentConstraint1.' + side + 'ikArmIKMechanics01_jntW1')
        cmds.connectAttr(side + 'armSettings_ctrl.fkIkBlend', side + 'armLowOut_jntNull_parentConstraint1.' + side + 'fkArmMechanics01_jntW0')

        #hand
        cmds.shadingNode('reverse', asUtility=True, n=side + 'handOut_jntNull_reverse')

        cmds.connectAttr(side + 'armSettings_ctrl.fkIkBlend', side + 'handOut_jntNull_reverse.inputX')
        cmds.connectAttr(side + 'handOut_jntNull_reverse.outputX', side + 'handOut_jntNull_parentConstraint1.' + side + 'ikArmIKMechanics02_jntW1')
        cmds.connectAttr(side + 'armSettings_ctrl.fkIkBlend', side + 'handOut_jntNull_parentConstraint1.' + side + 'fkArmMechanics02_jntW0')

        #######################################################################

        cmds.duplicate(side + 'ikLegIKMechanics00_jnt', rc=True)
        jnts = cmds.listRelatives(side + 'ikLegIKMechanics00_jnt1', ad=True)

        for jnt in jnts:
            
            if jnt == side + 'ikLegIKMechanics00_jnt1':
               pass
            
            elif jnt == side + 'ikLegIKMechanics01_jnt1':
               pass
            elif jnt == side + 'ikLegIKMechanics02_jnt1':
               pass
                   
            else:
                cmds.delete(jnt)
                
        cmds.rename(side + 'ikLegIKMechanics00_jnt1', side + 'legUpOut_jntNull')
        cmds.rename(side + 'ikLegIKMechanics01_jnt1', side + 'legLowOut_jntNull')
        cmds.rename(side + 'ikLegIKMechanics02_jnt1', side + 'footOut_jntNull')

        cmds.parent(side + 'legUpOut_jntNull', 'M_spineHipOut_jnt')

        cmds.parentConstraint(side + 'fkLegMechanics00_jnt', side + 'ikLegIKMechanics00_jnt', side + 'legUpOut_jntNull', mo=True)
        cmds.parentConstraint(side + 'fkLegMechanics01_jnt', side + 'ikLegIKMechanics01_jnt', side + 'legLowOut_jntNull', mo=True)
        cmds.parentConstraint(side + 'fkLegMechanics02_jnt', side + 'ikLegIKMechanics02_jnt', side + 'footOut_jntNull', mo=True)

        #connect FK/IK blends

        #up
        cmds.shadingNode('reverse', asUtility=True, n=side + 'legUpOut_jntNull_reverse')

        cmds.connectAttr(side + 'legSettings_ctrl.fkIkBlend', side + 'legUpOut_jntNull_reverse.inputX')
        cmds.connectAttr(side + 'legUpOut_jntNull_reverse.outputX', side + 'legUpOut_jntNull_parentConstraint1.' + side + 'ikLegIKMechanics00_jntW1')
        cmds.connectAttr(side + 'legSettings_ctrl.fkIkBlend', side + 'legUpOut_jntNull_parentConstraint1.' + side + 'fkLegMechanics00_jntW0')

        #low
        cmds.shadingNode('reverse', asUtility=True, n=side + 'legLowOut_jntNull_reverse')

        cmds.connectAttr(side + 'legSettings_ctrl.fkIkBlend', side + 'legLowOut_jntNull_reverse.inputX')
        cmds.connectAttr(side + 'legLowOut_jntNull_reverse.outputX', side + 'legLowOut_jntNull_parentConstraint1.' + side + 'ikLegIKMechanics01_jntW1')
        cmds.connectAttr(side + 'legSettings_ctrl.fkIkBlend', side + 'legLowOut_jntNull_parentConstraint1.' + side + 'fkLegMechanics01_jntW0')

        #foot
        cmds.shadingNode('reverse', asUtility=True, n=side + 'footOut_jntNull_reverse')

        cmds.connectAttr(side + 'legSettings_ctrl.fkIkBlend', side + 'footOut_jntNull_reverse.inputX')
        cmds.connectAttr(side + 'footOut_jntNull_reverse.outputX', side + 'footOut_jntNull_parentConstraint1.' + side + 'ikLegIKMechanics02_jntW1')
        cmds.connectAttr(side + 'legSettings_ctrl.fkIkBlend', side + 'footOut_jntNull_parentConstraint1.' + side + 'fkLegMechanics02_jntW0')


def BDP_palmAttr_rigMod(side):
    
    ##########################################################################################
    '''
    M_lipsMuzzle_ctrl
    
    side = "L_"

    '''
    ##########################################################################################
    
    palmOffsets = cmds.ls(side + 'hand*00_offset')

    for palmOffset in palmOffsets:
        
        if palmOffset == side + 'handThumb00_offset':
            pass
            
        else:
            #print(palmOffset)
            
            attrs = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']
            for attr in attrs:
            
                # Select the driver object and attribute
                #driver_object = side + "hand_ctrl"
                #print(palmOffset + '.' + attr)
                
                driven_object = palmOffset 
                driver_object = side + "hand_ctrl"
                
                driver_attribute = 'palmTwist'
                driven_attribute = attr
                
                # Set the initial values for the driver and driven attributes
                cmds.setAttr(driver_object + "." + driver_attribute, 0)
                cmds.setAttr(driven_object + "." + driven_attribute, 0)

                # Create the first driven key
                cmds.setDrivenKeyframe(driven_object + "." + driven_attribute, 
                                       currentDriver=driver_object + "." + driver_attribute, 
                                       driverValue=0, value=0)

                # Set the driver attribute to a new value and create another driven key
                cmds.setAttr(driver_object + "." + driver_attribute, 0)
                cmds.setDrivenKeyframe(driven_object + "." + driven_attribute, 
                                       currentDriver=driver_object + "." + driver_attribute, 
                                       driverValue=15, value=0)
                                       
                cmds.setAttr(driver_object + "." + driver_attribute, 0)
                cmds.setDrivenKeyframe(driven_object + "." + driven_attribute, 
                                       currentDriver=driver_object + "." + driver_attribute, 
                                       driverValue=-15, value=0)
                                   
def BDP_pecLift_rigMod(side):
    
    ##########################################################################################
    '''
    M_lipsMuzzle_ctrl
    
    '''
    ##########################################################################################
    
    attrs = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']
    
    for attr in attrs:
            
        # Select the driver object and attribute
        driver_object = side + "clavicle_ctrl"
        driver_attribute = attr

        # Select the driven object and attribute
        driven_object = side + "breast_offset"
        
        if attr[0] == 'r':
        
            for tattr in attrs:
                
                driver_attribute = attr
                driven_attribute = tattr
                
                #print(side + "clavicle_ctrl" + "." + driver_attribute + "------->" + side + "breast_offset" + "." + driven_attribute)
                   
                # Set the initial values for the driver and driven attributes
                cmds.setAttr(driver_object + "." + driver_attribute, 0)
                cmds.setAttr(driven_object + "." + driven_attribute, 0)

                # Create the first driven key
                cmds.setDrivenKeyframe(driven_object + "." + driven_attribute, 
                                       currentDriver=driver_object + "." + driver_attribute, 
                                       driverValue=0, value=0)

                # Set the driver attribute to a new value and create another driven key
                cmds.setAttr(driver_object + "." + driver_attribute, 10)
                cmds.setDrivenKeyframe(driven_object + "." + driven_attribute, 
                                       currentDriver=driver_object + "." + driver_attribute, 
                                       driverValue=10, value=10)
                                       
                cmds.setAttr(driver_object + "." + driver_attribute, -10)
                cmds.setDrivenKeyframe(driven_object + "." + driven_attribute, 
                                       currentDriver=driver_object + "." + driver_attribute, 
                                       driverValue=-10, value=-10)
                
        elif attr[0] == 't':
            
                print(side + "clavicle_ctrl" + "." + attr + "------->" + side + "breast_offset" + "." + attr)
                
 
    
def BDP_lipsMuzzleRot_rigMod():
    
    ##########################################################################################
    '''
    M_lipsMuzzle_ctrl
    
    '''
    ##########################################################################################
    
    pass