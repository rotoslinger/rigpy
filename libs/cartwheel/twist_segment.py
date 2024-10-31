import importlib
from maya import cmds, mel
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma

def vec_lerp(vec_a, vec_b, lerp_amt=0.5) -> om.MVector:
    '''
    :param vec_a (om2.MVector): source
    :param vec_b (om2.MVector): target
    :param lerp_amt: A float (usually) between 0 and 1 to control the interpolation.
                     Not clamped - so avoid unintentional over/undershooting.
    '''
    return ((vec_a - vec_b) * lerp_amt) + vec_a


def lerp_weight_range(num_values, start=0.0, end=1.0):
    # generic linear interpolate
    # L(t)=(1-t)·a+t·b lerp between two values, a and b, based on interp param t
    return [(start + (t * (end - start) / (num_values + 1))) for t in range(1, num_values + 1)]


def get_jnt_orient(jnt):
    selection = om.MSelectionList()
    selection.add(jnt)
    joint_dag_path = selection.getDagPath(0)
    joint_fn = oma.MFnIkJoint(joint_dag_path)
    joint_orient = joint_fn.orientation()
    return joint_orient


def set_jnt_orient(jnt, orient):
    selection = om.MSelectionList()
    selection.add(jnt)
    joint_dag_path = selection.getDagPath(0)
    joint_fn = oma.MFnIkJoint(joint_dag_path)
    joint_orient = joint_fn.setOrientation(orient)
    return joint_orient


def clone_new_jnt(src_jnt, new_jnt_name, parent) -> tuple: # type str,
    matrix = cmds.getAttr(f'{src_jnt}.worldMatrix')
    # ran into a few issues with parents and spaces using cmds, going with OpenMaya for now :(
    orient = get_jnt_orient(src_jnt)
    new_jnt = cmds.createNode('joint', parent=parent, name=new_jnt_name)
    cmds.setAttr(f'{new_jnt}.worldMatrix', *matrix, type='matrix')
    set_jnt_orient(jnt=new_jnt, orient=orient)
    return new_jnt, orient


def create_twist_segment(start_joint, end_joint, num_tw_jnts=5, suffix='Tw') -> tuple:
    # return tuple : list of jnts, list of floats
    # pargs given in order of parent,child - example: arm,elbow || elbow,hand
    vec_start = cmds.xform(start_joint, query=True, worldSpace=True, translation=True)
    vec_end = cmds.xform(end_joint, query=True, worldSpace=True, translation=True)

    vec_start = om.MVector(vec_start)
    vec_end = om.MVector(vec_end)

    idx = 3
    name = 'jnt'
    suffix = f'{suffix}{idx:02}'  # Output will be 'jnt03'

    weighted_vals = lerp_weight_range(num_tw_jnts)

    for idx, weight in enumerate(num_tw_jnts):
        suffix = f'{suffix}{idx:02}'
        jnt_position = vec_lerp()

    # Calculate the vector from start to end position using om2
    segment_vector = vec_start-vec_end


    # Placeholder for additional functionality
    ''''''

# Example call
#create_twist_segment(start_joint='LeftArm', end_joint='LeftForeArm', number_of_twist_joints=5)


r'''

twist segment, srototype that has a start jnt, end jnt, and n number of tw between the two.

Hier looks like : StartJnt->Tw00->Tw01->Tw02->Tw03->Tw05->EndJnt  (all parented to StartJnt).

Twist count isn't limited but defaults to 5.

StartJnt, EndJnt are parentConstrained to  LeftArm, LeftForeArm.

As the arm jnts move or rotate you get twist and stretch between.

You don't have to worry about multiple IK/FK joint chains because these could be constrained to your skin joints.

The idea is that it doesn't interfere with any structural rigging

goes along for the ride without creating any dependencies or complicating any IK/FK switching.

'''