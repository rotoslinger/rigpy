import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as omanim

# Global variables to hold last curves
SHAPESImportLastCurveUL = ""
SHAPESImportLastCurveUA = ""
SHAPESImportLastCurveUU = ""

def SHAPESImportGetLastCurve(init):
    global SHAPESImportLastCurveUL, SHAPESImportLastCurveUA, SHAPESImportLastCurveUU

    lastCurveUL = ""
    lastCurveUA = ""
    lastCurveUU = ""

    # List all animation curves in the scene
    curves = cmds.ls(type="animCurve")
    
    for c in curves:
        if cmds.gmatch(c, "animCurveUL*"):
            lastCurveUL = c
        elif cmds.gmatch(c, "animCurveUA*"):
            lastCurveUA = c
        elif cmds.gmatch(c, "animCurveUU*"):
            lastCurveUU = c

    if init == 1:
        # Initialize global variables
        SHAPESImportLastCurveUL = lastCurveUL
        SHAPESImportLastCurveUA = lastCurveUA
        SHAPESImportLastCurveUU = lastCurveUU
        return ""

    # Compare with last saved curves and update if changed
    if lastCurveUL != SHAPESImportLastCurveUL:
        SHAPESImportLastCurveUL = lastCurveUL
        return lastCurveUL
    elif lastCurveUA != SHAPESImportLastCurveUA:
        SHAPESImportLastCurveUA = lastCurveUA
        return lastCurveUA
    elif lastCurveUU != SHAPESImportLastCurveUU:
        SHAPESImportLastCurveUU = lastCurveUU
        return lastCurveUU
    else:
        return ""

_API_ATTRS = {  'curve' : {'isStatic', 'isWeighted', 'preInfinityType', 'postInfinityType'},
                'key'   : {'value', 'isBreakdown', 'tangentsLocked', 'inTangentType', 'outTangentType'}}



def _animCurveData(mcurve):
    data = {attr:getattr(mcurve, attr) for attr in _API_ATTRS['curve']}
    data['keys'] = {k_i : _animCurveKeyData(mcurve, k_i) for k_i in range(mcurve.numKeys)}
    return data

def _animCurveKeyData(mcurve, index):
    data = {attr:getattr(mcurve, attr)(index) for attr in _API_ATTRS['key']}
    data.update(time=mcurve.input(index).value,
                in_tangent={'xy' : mcurve.getTangentXY(index, True)},
                out_tangent={'xy' : mcurve.getTangentXY(index, False)})
    return data

data = _animCurveData(mcurve)



from maya import cmds

def getAnimCurveData(dg_name, mcurve):
    outputs = cmds.listConnections(dg_name, s=False, d=True, p=True, scn=True)
    dag_outputs = cmds.listConnections(dg_name, s=False, d=True, p=True, scn=True, type='dagNode')
    is_blended = False
    for output in outputs:
        if not cmds.nodeType(output)=='pairBlend':
            continue
        is_blended = True
        pb_node, plug = output.split('.')
        pb_plug = plug.replace('in', 'out')[:-1]
        pb_outputs = cmds.listConnections('{}.{}'.format(pb_node, pb_plug), s=False, d=True, p=True, scn=True) or dag_outputs
        output = pb_outputs[0]
    if not is_blended:
        output = outputs[0]
    output_node, output_attr = output.split('.')
    destination = {'node':cmds.ls(output_node, l=True)[0], 'attr':cmds.attributeQuery(output_attr, node=output_node, ln=True)}
    data = _animCurveData(mcurve)
    return {'outputs':outputs, 'is_blended':is_blended, 'destination':destination, 'data':data}

data = getAnimCurveData(mcurve.name(), mcurve)


import re
def _toUnderscores(string):
    parts = re.findall('[A-Z]?[a-z]+', string)
    for i, p in enumerate(parts):
        parts[i] = p.lower()
    return '_'.join(parts)

_API_SOURCE = { 'curve' : {'isStatic', 'isWeighted', 'preInfinityType', 'postInfinityType'},
                'key'   : {'value', 'isBreakdown', 'tangentsLocked', 'inTangentType', 'outTangentType'}}

_API_ATTRS = {level:{_toUnderscores(attr):attr for attr in _API_ATTRS[level]} for level in _API_SOURCE}



def _animCurveData(mcurve):
    data = {at_k:getattr(mcurve, at_api) for at_k, at_api in _API_ATTRS['curve'].iteritems()}

def _animCurveKeyData(mcurve, index):
    data = {at_k:getattr(mcurve, at_api)(index) for at_k, at_api in _API_ATTRS['key'].iteritems()}



def setAnimCurveData(mcurve, data):
    mcurve.setIsWeighted(data['is_weighted'])
    mcurve.setPreInfinityType(data['pre_infinity_type'])
    mcurve.setPostInfinityType(data['post_infinity_type'])
    for k_i, k_values in data['keys'].iteritems():
        k_time = om.MTime(k_values['time'])
        if not mcurve.find(k_time): #if there is no key at the specified source frame, we will create a new one
            mcurve.addKey(k_time, k_values['value'])
        _setAnimCurveKeyData(mcurve, mcurve.find(k_time), k_values) #notice that we get the actual index with mcurve.find(k_time), this allows us to merge curve data into already populated curves.

def _setAnimCurveKeyData(mcurve, index, data):
    mcurve.setTangentsLocked(index, False)
    mcurve.setInTangentType(index, data['in_tangent_type'])
    x, y = data['in_tangent']['xy']
    mcurve.setTangent(index, x, y, True, convertUnits=False) #IN TANGENT
    mcurve.setOutTangentType(index, data['out_tangent_type'])
    x, y = data['out_tangent']['xy']
    mcurve.setTangent(index, x, y, False, convertUnits=False) #OUT TANGENT
    mcurve.setIsBreakdown(index, data['is_breakdown'])
    if data['tangents_locked']:
        mcurve.setTangentsLocked(index, True)
        
new_curve = omanim.MFnAnimCurve()
new_curve.create(omanim.MFnAnimCurve.kAnimCurveTL) #we will test our data on a time to linear curve
setAnimCurveData(new_curve, data)



from maya import cmds

def getAnimCurveData(dg_name, mcurve):
    outputs = cmds.listConnections(dg_name, s=False, d=True, p=True, scn=True)
    dag_outputs = cmds.listConnections(dg_name, s=False, d=True, p=True, scn=True, type='dagNode')
    is_blended = False
    for output in outputs:
        if not cmds.nodeType(output)=='pairBlend':
            continue
        is_blended = True
        pb_node, plug = output.split('.')
        pb_plug = plug.replace('in', 'out')[:-1]
        pb_outputs = cmds.listConnections('{}.{}'.format(pb_node, pb_plug), s=False, d=True, p=True, scn=True) or dag_outputs
        output = pb_outputs[0]
    if not is_blended:
        output = outputs[0]
    output_node, output_attr = output.split('.')
    destination = {'node':cmds.ls(output_node, l=True)[0], 'attr':cmds.attributeQuery(output_attr, node=output_node, ln=True)}
    data = _animCurveData(mcurve)
    return {'outputs':outputs, 'is_blended':is_blended, 'destination':destination, 'data':data}

data = getAnimCurveData(mcurve.name(), mcurve)
