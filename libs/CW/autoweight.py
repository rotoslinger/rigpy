import maya.api.OpenMaya as om

# Get the MObject for a mesh
def get_dag_path(obj_name):
    selection_list = om.MSelectionList()
    selection_list.add(obj_name)
    return selection_list.getDagPath(0)

# Replace 'pSphere1' with the name of your mesh object
mesh_name = 'pSphere1'
dag_path = get_dag_path(mesh_name)

# Create the MItMeshVertex iterator
vertex_iter = om.MItMeshVertex(dag_path)

# Iterate over each vertex in the mesh
while not vertex_iter.isDone():
    # Get the vertex position
    position = vertex_iter.position(om.MSpace.kWorld)
    print(f'Vertex {vertex_iter.index()}: Position = {position}')
    
    # Move to the next vertex
    vertex_iter.next()


def get_closest_point_on_curve(curve_name, point):
    # Get the MObject for the curve
    selection_list = om.MSelectionList()
    selection_list.add(curve_name)
    curve_dag_path = selection_list.getDagPath(0)

    # Create an MFnNurbsCurve function set for the curve
    curve_fn = om.MFnNurbsCurve(curve_dag_path)

    # Convert the input point to an MPoint
    target_point = om.MPoint(point[0], point[1], point[2])

    # Find the closest point on the curve
    closest_point = curve_fn.closestPoint(target_point, space=om.MSpace.kWorld)

    # Get the parameter at the closest point on the curve
    param = curve_fn.findParamFromPoint(closest_point, space=om.MSpace.kWorld)

    return closest_point, param

# Example usage
curve_name = 'nurbsCurve1'  # Replace with your curve's name
point = (1.0, 2.0, 3.0)     # Replace with your target point
closest_point, param = get_closest_point_on_curve(curve_name, point)
print(f"Closest point: {closest_point}")
print(f"Parameter at closest point: {param}")

'''
Long Triangle Arrows
Black Right◅Pointing Pointer: ► (U+25BA)
Black Left◅Pointing Pointer: ◄ (U+25C4)
White Right◅Pointing Pointer: ▻ (U+25BB)
White Left◅Pointing Pointer: ◅ (U+25C5)
Filled and Open Triangle Arrows
Right◅Pointing Small Triangle: ▸ (U+25B8)
Left◅Pointing Small Triangle: ◂ (U+25C2)
Narrow Triangle Arrows
Right Triangle◅Headed Arrow: ⇾ (U+21FE)
Left Triangle◅Headed Arrow: ⇽ (U+21FD)
Vertical Triangle Arrows
Up◅Pointing Small Triangle: ▴ (U+25B4)
Down◅Pointing Small Triangle: ▾ (U+25BE)

'''

class WeightCurve:
    def __init__(self, mesh, joints, dir='-x'):

        self.mesh=mesh
        self.joints=joints
        self.dir=dir
        self.sort_joints()

    def get_side(self):
        self.sorted_joints[0]

    def sort_joints(self):
        '''
        sorts joints based on a direction
        -x dir is ◁○◁○◁○    
        +x dir is ▷○▷○▷○
        -y dir is ↓
        +y dir is ↑
        -z dir forward (depth negs)
        +z dir is backward (depth pos)
        diagonal or more complex directions aren't yet supported.
        '''
        self.sorted_joints = []
        
