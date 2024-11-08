'''
I found the answer for those of us using maya 2019:

Open the file here: C:\Program Files\Autodesk\Maya2019\scripts\others\hikDefinitionOperations.mel
Use those procedures. 


To create a control rig you will find the correct code here: 
C:\Program Files\Autodesk\Maya2019\scripts\others\hikCharacterControlsUI.mel

You may need to source the files in Maya first. A post mentions how to do that here: https://forums.autodesk.com/t5/maya-animation-and-rigging/pythonic-mel-way-to-retarget-hik/td-p/7609...

so this code worked for me:
'''
import maya.cmds as cmds
import maya.mel as mel
# Source the following scripts. If the code fails, then you'll have to load them and run them:
MAYA_LOCATION = os.environ['MAYA_LOCATION']
mel.eval('source "'+MAYA_LOCATION+'/scripts/others/hikGlobalUtils.mel"')
mel.eval('source "'+MAYA_LOCATION+'/scripts/others/hikCharacterControlsUI.mel"')
mel.eval('source "'+MAYA_LOCATION+'/scripts/others/hikDefinitionOperations.mel"')

#mel.eval('DeleteSkeletonDefinition();')
mel.eval('hikCreateDefinition()')

# -- Add joints to Definition.
mel.eval('setCharacterObject("root", "Character1",0,0);')
mel.eval('setCharacterObject("pelvis", "Character1",1,0);')
mel.eval('setCharacterObject("thigh_l", "Character1",2,0);')
mel.eval('setCharacterObject("calf_l", "Character1",3,0);')
mel.eval('setCharacterObject("foot_l", "Character1",4,0);')
mel.eval('setCharacterObject("thigh_r", "Character1",5,0);')
mel.eval('setCharacterObject("calf_r", "Character1",6,0);')
mel.eval('setCharacterObject("foot_r", "Character1",7,0);')
mel.eval('setCharacterObject("spine_01", "Character1",8,0);')
mel.eval('setCharacterObject("upperarm_l", "Character1",9,0);')
mel.eval('setCharacterObject("lowerarm_l", "Character1",10,0);')
mel.eval('setCharacterObject("hand_l", "Character1",11,0);')
mel.eval('setCharacterObject("upperarm_r", "Character1",12,0);')
mel.eval('setCharacterObject("lowerarm_r", "Character1",13,0);')
mel.eval('setCharacterObject("hand_r", "Character1",14,0);')
mel.eval('setCharacterObject("head", "Character1",15,0);')
mel.eval('setCharacterObject("ball_l", "Character1",16,0);')
mel.eval('setCharacterObject("ball_r", "Character1",17,0);')
mel.eval('setCharacterObject("clavicle_l", "Character1",18,0);')
mel.eval('setCharacterObject("clavicle_r", "Character1",19,0);')
mel.eval('setCharacterObject("neck_01", "Character1",20,0);')
#21 and 22 are extra wrists
mel.eval('setCharacterObject("spine_02", "Character1",23,0);')
mel.eval('setCharacterObject("spine_03", "Character1",24,0);')
#25-32 are additional spines
#33-42 are additional necks
mel.eval('setCharacterObject("thumb_01_l", "Character1",50,0);')
mel.eval('setCharacterObject("thumb_02_l", "Character1",51,0);')
mel.eval('setCharacterObject("thumb_03_l", "Character1",52,0);')
mel.eval('setCharacterObject("thumb_04_l_Jx", "Character1",53,0);')
mel.eval('setCharacterObject("index_01_l", "Character1",54,0);')
mel.eval('setCharacterObject("index_02_l", "Character1",55,0);')
mel.eval('setCharacterObject("index_03_l", "Character1",56,0);')
mel.eval('setCharacterObject("index_04_l_Jx", "Character1",57,0);')
mel.eval('setCharacterObject("middle_01_l", "Character1",58,0);')
mel.eval('setCharacterObject("middle_02_l", "Character1",59,0);')
mel.eval('setCharacterObject("middle_03_l", "Character1",60,0);')
mel.eval('setCharacterObject("middle_04_l_Jx", "Character1",61,0);')
mel.eval('setCharacterObject("ring_01_l", "Character1",62,0);')
mel.eval('setCharacterObject("ring_02_l", "Character1",63,0);')
mel.eval('setCharacterObject("ring_03_l", "Character1",64,0);')
mel.eval('setCharacterObject("ring_04_l_Jx", "Character1",65,0);')
mel.eval('setCharacterObject("pinky_01_l", "Character1",66,0);')
mel.eval('setCharacterObject("pinky_02_l", "Character1",67,0);')
mel.eval('setCharacterObject("pinky_03_l", "Character1",68,0);')
mel.eval('setCharacterObject("pinky_04_l_Jx", "Character1",69,0);')
#70-73 is left hand 6th finger
mel.eval('setCharacterObject("thumb_01_r", "Character1",74,0);')
mel.eval('setCharacterObject("thumb_02_r", "Character1",75,0);')
mel.eval('setCharacterObject("thumb_03_r", "Character1",76,0);')
mel.eval('setCharacterObject("thumb_04_r_Jx", "Character1",77,0);')
mel.eval('setCharacterObject("index_01_r", "Character1",78,0);')
mel.eval('setCharacterObject("index_02_r", "Character1",79,0);')
mel.eval('setCharacterObject("index_03_r", "Character1",80,0);')
mel.eval('setCharacterObject("index_04_r_Jx", "Character1",81,0);')
mel.eval('setCharacterObject("middle_01_r", "Character1",82,0);')
mel.eval('setCharacterObject("middle_02_r", "Character1",83,0);')
mel.eval('setCharacterObject("middle_03_r", "Character1",84,0);')
mel.eval('setCharacterObject("middle_04_r_Jx", "Character1",85,0);')
mel.eval('setCharacterObject("ring_01_r", "Character1",86,0);')
mel.eval('setCharacterObject("ring_02_r", "Character1",87,0);')
mel.eval('setCharacterObject("ring_03_r", "Character1",88,0);')
mel.eval('setCharacterObject("ring_04_r_Jx", "Character1",89,0);')
mel.eval('setCharacterObject("pinky_01_r", "Character1",90,0);')
mel.eval('setCharacterObject("pinky_02_r", "Character1",91,0);')
mel.eval('setCharacterObject("pinky_03_r", "Character1",92,0);')
mel.eval('setCharacterObject("pinky_04_r_Jx", "Character1",93,0);')
#94-97 is 6th right hand finger
#98-101 is 6th left foot toe
#102-121 are left foot toes
#122-125 is 6th right foot toe
#126-145 are right foot toes
#146 is left hand thumb 0

mel.eval('hikUpdateDefinitionUI;')
mel.eval('LockSkeletonDefinition();')

mel.eval('hikCreateControlRig;')
cmds.parent('Character1_Ctrl_Reference', 'Character1_Root_CNT')

