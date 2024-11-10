import random,math

import maya.OpenMaya as om

import rpdecorator

DOC_HEADER = '''
Arrows represent 2-d directional vectors at euler angles:
       0, 45, 90, 135, 180, -180, -135, -90, -45
                         ↖ ↑ ↗  
                         ← • →  
                         ↙ ↓ ↘  
'''

# Helper function to calculate the dot product of two vectors
def dot_product(v1, v2):
    return v1[0] * v2[0] + v1[1] * v2[1]

# Define all pairs and used pairs at a higher scope
all_pairs = []  # This will hold all possible unique pairs of angles
used_pairs = []  # This will track used pairs

# Create all possible vector pairs (angle1, angle2) without repeats
def initialize_pairs():
    global all_pairs
    angles = [0, 45, 90, 135, 180, -180, -135, -90, -45]
    all_pairs = [(a1, a2) for i, a1 in enumerate(angles) for a2 in angles[i+1:]]
    used_pairs.clear()  # Reset the used pairs

# Function to print the documentation and vectors
@rpdecorator.print_bookends
def print_dot_product_documentation():

    # If all pairs haven't been initialized, initialize them
    if not all_pairs:
        initialize_pairs()

    # Dictionary of Euler angles to vectors (angle: vector)
    angle_to_vector_dict = {
        0: (0, 1),
        45: (1, 1),
        90: (1, 0),
        135: (1, -1),
        180: (0, -1),
        -180: (0, -1),
        -135: (-1, -1),
        -90: (-1, 0),
        -45: (-1, 1)
    }

    # Unicode symbols for arrows and points
    arrows = {
        0: '↑', 45: '↗', 90: '→', 135: '↘', 180: '↓', 
        -180: '↑', -135: '↖', -90: '←', -45: '↙'
    }

    # Create the directional square with center point
    print(DOC_HEADER)

    # Check if there are any pairs left to choose from
    if not all_pairs:
        print("\nAll vector pairs have been compared.")
        return

    # Pick a random unused pair
    angle1, angle2 = random.choice(all_pairs)
    all_pairs.remove((angle1, angle2))  # Remove the chosen pair from the list of available pairs
    used_pairs.append((angle1, angle2))  # Add to the list of used pairs

    # Get the vectors for the chosen angles from the dictionary
    vector1 = angle_to_vector_dict[angle1]
    vector2 = angle_to_vector_dict[angle2]

    # Calculate the dot product
    dot_prod = dot_product(vector1, vector2)

    # Visual representation with arrows and dot product
    print(f"\n{arrows[angle1]} • {arrows[angle2]} == {dot_prod:.2f}")

    # Print the arrows and their corresponding vectors
    print(f"\nArrow 1: {arrows[angle1]} Vector@ ((0,0) - ({vector1[0]},{vector1[1]}))")
    print(f"Arrow 2: {arrows[angle2]} Vector@ ((0,0) - ({vector2[0]},{vector2[1]}))")

    # Print the dot product formula
    print(f"\nDot product formula:")
    print(f"(({vector1[0]},{vector1[1]}) - (0,0)) dot ({vector2[0]},{vector2[1]}) - (0,0)) = {dot_prod:.2f}")
    # Concise description of dot product sign
    if dot_prod > 0:
        print("\nThe dot product is positive.\nThe vectors are pointing in a similar direction (i.e. acute).")
    elif dot_prod < 0:
        print("\nThe dot product is negative.\nThe vectors are pointing toward each other (i.e. obtuse).")
    else:
        print("\nThe dot product is zero.\nThe vectors are perpendicular(i.e. orthogonal).")
########################################## Usage example ###########################################
# from importlib import reload
# from CW import auto_doc
# reload(auto_doc)
# dot_product.print_dot_product_documentation()
####################################################################################################import maya.OpenMaya as om

def vector_relation(v1, v2):
    # Convert tuples to MVector objects
    v1 = om.MVector(v1[0], v1[1])
    v2 = om.MVector(v2[0], v2[1])
    
    # Compute the dot product
    dot_prod = v1 * v2
    
    # Calculate magnitudes
    mag_v1 = v1.length()
    mag_v2 = v2.length()

    # Calculate the cosine of the angle
    cos_theta = dot_prod / (mag_v1 * mag_v2)
    
    # Determine the relation based on the cosine of the angle
    if cos_theta > 0.5:
        return 1  # Vectors are somewhat facing (acute angle)
    elif cos_theta < -0.5:
        return -1  # Vectors are somewhat facing away (obtuse angle)
    else:
        return 0  # Vectors are perpendicular (right angle)

# # Example usage
# v1 = (1, 0)
# v2 = (2, 1)
# relation = vector_relation(v1, v2)
# print(f"The relation is: {relation}")  # 1 for somewhat facing, -1 for somewhat facing away, 0 for perpendicular



def point_inside_or_outside(point, mesh_point, normal):
    # Convert the point and mesh_point to MVector objects
    point = om.MVector(point[0], point[1], point[2])
    mesh_point = om.MVector(mesh_point[0], mesh_point[1], mesh_point[2])
    normal = om.MVector(normal[0], normal[1], normal[2])
    
    # Calculate the directional vector from the point to the mesh point
    directional_vector = mesh_point - point  # mesh_point - point
    
    # Compute the dot product of the directional vector with the normal
    dot_prod = directional_vector * normal
    
    # Determine if the point is inside, outside, or on the surface
    if dot_prod > 0:
        return True  # Point is inside the mesh
    elif dot_prod < 0:
        return False  # Point is outside the mesh
    else:
        return False  # Point is exactly on the surface

# # Example usage
# point = (1, 1, 1)  # Point to check (can be inside or outside the mesh)
# mesh_point = (2, 2, 2)  # A point on the surface of the mesh (for example, a vertex)
# normal = (0, 1, 0)  # The normal at the mesh point (pointing up along the y-axis)

# result = point_inside_or_outside(point, mesh_point, normal)
# print(f"The point is: {result}")
