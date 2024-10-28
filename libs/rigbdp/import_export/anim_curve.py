import json
import maya.cmds as cmds
import maya.api.OpenMayaAnim as omanim
from collections import defaultdict

SDK_EXPORT_ATTRS = { 'curve' : {'isStatic', 'isWeighted', 'preInfinityType', 'postInfinityType'},
                     'key'   : {'value', 'isBreakdown', 'tangentsLocked', 'inTangentType', 'outTangentType'}}


SDK_EXPORT_ATTRS = ['isStatic', 'isWeighted', 'preInfinityType', 'postInfinityType',
                    'value', 'isBreakdown', 'tangentsLocked', 'inTangentType', 'outTangentType']

'''
This module has two major purposes.  They are:
1. Export all set driven keys in a maya scene to a json dictionary
2. Import all set driven keys in a maya scene from a json dictionary

Export
There are certain export rules that must be followed:

1. --- all driver nodes must exist before sdk import.
2. --- all driven nodes must exist before sdk import.
3. --- upon export the set driven key anim curve must have both an input 
       and output connection.  If this is not so, the set 
       driven key will not be exported.

For the most part, this is it. I would recommend a somewhat descriptive
naming convention, but it is by no means required.

It is important to note, if a driven connection has multiple drivers, a
blend node is automatically created between the set driven keyframe and
the driven connection. This information will be saved in the json export
dict and will be used to reconstruct the sdk upon reload.


Import
Import rules are much the same as export rules:
1. --- all driver and driven nodes must exist, with the exception of any
       blendWeighted nodes, which will be created if they don't yet exist.

As a side note, it is important to keep in mind the chronological order
of when the sdk is created. Any scripts which create nodes that are used
to drive, or be driven need to have already be run. Any import functions
should be run as late as they can be in any build process they are used in.

'''

def rename_blend_weighted_nodes(debug=False)->None:
    # Find all blendWeighted nodes
    blend_weighted_nodes = cmds.ls(type='blendWeighted')
    for node in blend_weighted_nodes:
        if '_' in node: continue # '_' means the node has already been renamed, skip
        
        connections = cmds.listConnections(f'{node}.output', plugs=True, skipConversionNodes=True) or []

        # Filter out node editor garbage connections
        connections = [conn for conn in connections if "MayaNodeEditor" not in conn]

        # if no connections remain we can't rename, so skip
        if not connections:continue

        # only the first index, for the sake of readability
        connection = connections[0]

        # derive name from connections
        driven_node, attribute = connection.split('.')[0],connection.split('.')[1]
        new_name = f"{driven_node}_{attribute}_blendWeighted"

        cmds.rename(node, new_name)
        if debug: print(f"Renamed {node} to {new_name}")

def rename_sdk(sdk, input, output, debug=False)-> None:

    # we can assume that the key has already been renamed if it has '_' in it
    if '_' in sdk: return sdk

    input_node, input_attr = input.split('.')
    output_node, output_attr = output.split('.')

    new_name = f'{input_node}_{input_attr}_to_{output_node}_{output_attr}_sdk'
    cmds.rename(sdk, new_name)

    return new_name


def get_blend_weighted_in_out(blend_weighted_node) -> dict:

    # we are going to look at both in and out so if the node is an attribute, get the node side
    if '.' in blend_weighted_node:
        blend_weighted_node = blend_weighted_node.split('.')[0]

    # get the in and out connections
    blend_weighted_input = cmds.listConnections(f'{blend_weighted_node}.input', # positional arg
                                                source=True, 
                                                plugs=True, 
                                                skipConversionNodes=True) or []
    blend_weighted_output = cmds.listConnections(f'{blend_weighted_node}.output', # positional arg
                                                 destination=True,
                                                 plugs=True, 
                                                 skipConversionNodes=True) or []
    
    # if either is disconnected we aren't interested anymore
    if not blend_weighted_output or not blend_weighted_input:return None, None

    return {blend_weighted_node:blend_weighted_input}, blend_weighted_output


SDK_EXPORT_ATTRS = { 'curve' : {'isStatic', 'isWeighted', 'preInfinityType', 'postInfinityType'},
                     'key'   : {'value', 'isBreakdown', 'tangentsLocked', 'inTangentType', 'outTangentType'}}


SDK_EXPORT_ATTRS = ['isStatic', 'isWeighted', 'preInfinityType', 'postInfinityType',
                    'value', 'isBreakdown', 'tangentsLocked', 'inTangentType', 'outTangentType']


def get_all_keyframe_data(anim_curve) -> dict:
    # time=(None,None) is a short form to specify all keys.

    pass

def get_all_sdk():
    anim_curves = cmds.ls(typ='animCurve')
    sdk_curves=[]
    sdk_connection_map = {}
    blend_input_map = {}
    for a_curve in anim_curves:
        input=f'{a_curve}.input'
        output=f'{a_curve}.output'
        # if the animCurve doesn't have both input and output attributes it is just a keyframe
        sdk_curves.append(a_curve)
        input = cmds.listConnections(a_curve, # positional arg
                                     source=True, 
                                     destination=False, 
                                     plugs=True, 
                                     skipConversionNodes=True)
        if not input: continue
        input=input[0]
        output = cmds.listConnections(a_curve, # parg
                                      source=False,
                                      destination=True,
                                      plugs=True,
                                      skipConversionNodes=True) or []
        if not output: continue
        output=output[0]
        blend_output = None
        final_output = output
        # if it is a blendWeighted node, get its output as the final output.
        if 'blendWeighted' in cmds.objectType(output):
            blend_input,blend_output=get_blend_weighted_in_out(output)
            key = list(blend_input)[0]
            if key not in blend_input_map.keys():
                blend_input_map[key] = blend_input[key]
        a_curve_type = cmds.objectType(a_curve)
        if blend_output:
            final_output = blend_output[0]

        a_curve = rename_sdk(a_curve,
                             input=input,
                             output=final_output)
        

        # INPUT :  null1.translateX
        # OUTPUT :  null2_scaleY_blendWeighted.input[0]
        # BLEND_OUTPUT :  ['null2.scaleY']
        sdk_connection_map[a_curve] = {'input':input, 'output':output, 'blend_output':blend_output, 'obj_type':a_curve_type}


        # for outputs, check if there are any connections that are blend weighted
        #sdk_connection_map[a_curve] = {'inputs':input,'outputs':output, '2ndary_inputs':[]}

        # print(a_curve)
        # print(input)
        # print(output)
        # ul ua uu
# setDrivenKeyframe -dv -90 -v 1 -cd L_arm05Out_jnt.rotateY -itt spline -ott spline M_jsh_base_body_geoShapes_blendShape.L_lowArm_ry_neg_90;



    # blend_input_map = common_connections(blend_input_map)
    print('blend_output_map : ', blend_input_map)
    # print('sdk_connection_map : ', sdk_connection_map)
    return sdk_connection_map, blend_input_map






#connectAttr -f null1.translateX animCurveUA1.input;
#connectAttr -f animCurveUA1.output null1.translateX;










def get_sdk_final_input(a_curve):
    input = cmds.setDrivenKeyframe(a_curve)
    output = cmds.setDrivenKeyframe(a_curve)
    






#cmds.ls(typ='animCurve')
#ccmds.setDrivenKeyframe('M_jsh_base_body_geoShapes_blendShape_L_index01_ry_neg_35_WD', q=True,)

#mds.setDrivenKeyframe( 'pCone1.tx', q=True, currentDriver=True )
#sdk = 'M_jsh_base_body_geoShapes_blendShape_L_index01_ry_neg_35_WD'
#driver = cmds.setDrivenKeyframe( sdk, q=True, driver=True )
#driven = cmds.setDrivenKeyframe( sdk, q=True, driven=True )

#print(driver)
#print(driven)


#cmds.select('M_jsh_base_body_geoShapes_blendShape_L_index01_ry_neg_35_WD')
#if an anim keyframe has input and output, you know it is a set driven key!






r'''

def _to_underscores(string):
    import re
    parts = re.findall('[A-Z]?[a-z]+', string)
    for i, p in enumerate(parts):
        parts[i] = p.lower()
    return '_'.join(parts)

# Define API attributes
_API_SOURCE = {
    'curve': {'isStatic', 'isWeighted', 'preInfinityType', 'postInfinityType'},
    'key': {'value', 'isBreakdown', 'tangentsLocked', 'inTangentType', 'outTangentType'}
}

_API_ATTRS = {level: {_to_underscores(attr): attr for attr in _API_SOURCE[level]} for level in _API_SOURCE}

def get_anim_curve_data(mcurve):
    """Extracts data from an animation curve and its connections."""
    data = {attr: getattr(mcurve, attr) for attr in _API_ATTRS['curve']}
    data['keys'] = {i: get_anim_curve_key_data(mcurve, i) for i in range(mcurve.numKeys)}

    # Get the input and output connections for the animation curve
    curve_name = mcurve.name()
    inputs = cmds.listConnections(curve_name, s=True, d=False, p=True) or []
    outputs = cmds.listConnections(curve_name, s=False, d=True, p=True) or []

    return {
        'curve_name': curve_name,
        'attributes': data,
        'input_connection': inputs[0] if inputs else None,
        'output_connection': outputs[0] if outputs else None
    }

def get_anim_curve_key_data(mcurve, index):
    """Extracts key data from a specific index in an animation curve."""
    data = {attr: getattr(mcurve, _API_ATTRS['key'][attr])(index) for attr in _API_ATTRS['key']}
    data.update({
        'time': mcurve.time(index).value,
        'in_tangent': mcurve.getTangentXY(index, True),
        'out_tangent': mcurve.getTangentXY(index, False)
    })
    return data

def export_anim_curves(filepath):
    """Exports all animation curves in the scene to a JSON file."""
    curves = cmds.ls(type='animCurve')
    anim_data = []

    for curve_name in curves:
        mcurve = omanim.MFnAnimCurve(cmds.ls(curve_name, uuid=True)[0])
        anim_data.append(get_anim_curve_data(mcurve))

    # Save to JSON file
    with open(filepath, 'w') as f:
        json.dump(anim_data, f, indent=4)

# Usage example
export_anim_curves('/path/to/anim_curves_export.json')



def set_anim_curve_data(mcurve, data):
    """Sets data on an existing or new animation curve based on exported JSON."""
    mcurve.setIsWeighted(data['attributes']['is_weighted'])
    mcurve.setPreInfinityType(data['attributes']['pre_infinity_type'])
    mcurve.setPostInfinityType(data['attributes']['post_infinity_type'])

    # Set keys
    for k_i, key_data in data['attributes']['keys'].items():
        key_time = om.MTime(key_data['time'])
        index = mcurve.find(key_time) or mcurve.addKey(key_time, key_data['value'])
        set_anim_curve_key_data(mcurve, index, key_data)

def set_anim_curve_key_data(mcurve, index, data):
    """Sets key data for a specific index in an animation curve."""
    mcurve.setTangentsLocked(index, False)
    mcurve.setInTangentType(index, data['in_tangent_type'])
    mcurve.setTangent(index, *data['in_tangent'], True)
    mcurve.setOutTangentType(index, data['out_tangent_type'])
    mcurve.setTangent(index, *data['out_tangent'], False)
    mcurve.setIsBreakdown(index, data['is_breakdown'])
    if data['tangents_locked']:
        mcurve.setTangentsLocked(index, True)

def import_anim_curves(filepath):
    """Imports animation curves from a JSON file, creating new curves if needed."""
    with open(filepath, 'r') as f:
        anim_data = json.load(f)

    for curve_data in anim_data:
        curve_name = curve_data['curve_name']
        existing_curves = cmds.ls(curve_name)

        if existing_curves:
            # Curve exists, retrieve and update it
            mcurve = omanim.MFnAnimCurve(cmds.ls(existing_curves[0], uuid=True)[0])
            set_anim_curve_data(mcurve, curve_data)
        else:
            # Create new curve and connect it
            new_curve = omanim.MFnAnimCurve()
            new_curve.create(omanim.MFnAnimCurve.kAnimCurveTL)
            set_anim_curve_data(new_curve, curve_data)

            # Handle input/output connections
            input_conn = curve_data.get('input_connection')
            output_conn = curve_data.get('output_connection')
            if input_conn:
                cmds.connectAttr(input_conn, f"{new_curve.name()}.input")
            if output_conn:
                cmds.connectAttr(f"{new_curve.name()}.output", output_conn)

# Usage example
import_anim_curves('/path/to/anim_curves_export.json')
'''