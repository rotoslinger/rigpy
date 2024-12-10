import json
import os
from maya import cmds


class SmartCopySkins:
    def __init__(self, source_mesh, target_mesh, skin_clusters):
        """
        Copies skin weights in an intelligent way. Adds skincluster and influences from a source
        mesh.
        example:
        SmartCopySkins(source_mesh='jsh_base_cloth_top_fabric_mesh',
                       target_mesh='jsh_base_cloth_top_fabric_low_mesh',
                       skin_clusters='jsh_base_cloth_top_fabric_mesh_bodyMechanics_skinCluster')
        SmartCopySkins(source_mesh='jsh_base_cloth_pants_fabric_mesh',
                       target_mesh='jsh_base_cloth_pants_fabric_low_mesh',
                       skin_clusters='jsh_base_cloth_pants_fabric_mesh_bodyMechanics_skinCluster')
        """
        # make sure it is a list...
        skin_clusters =  skin_clusters if isinstance(skin_clusters, list) else [skin_clusters]
        self.smart_copy_skinweights(source_mesh=source_mesh,
                                    target_mesh=target_mesh,
                                    skin_clusters=skin_clusters)

    def smart_copy_skinweights(self, source_mesh, target_mesh, skin_clusters=None):
        if skin_clusters is None:
            skin_clusters = self.get_skinclusters_on_mesh(source_mesh)

        src_skin_influences = {}
        src_connection_maps = {}
        target_skinclusters = []

        for idx, source_skincluster in enumerate(skin_clusters):
            # Retrieve the connection map directly without exporting it
            connection_map = self.get_compound_attr_connect_map(node=source_skincluster, compound_attr='matrix')
            src_connection_maps[f'{source_skincluster}_MAP'] = connection_map

            # Connect the source skin joints using the retrieved connection map
            self.connect_skin_joints(connection_map, source_skincluster)

            # Query influences of the source skin cluster
            influences = cmds.skinCluster(source_skincluster, query=True, influence=True)
            src_skin_influences[source_skincluster] = influences

        for source_skincluster in src_skin_influences:
            # Create or find the corresponding target skin cluster
            skincluster_new_name = source_skincluster.replace(source_mesh, target_mesh)
            target_skinclusters.append(skincluster_new_name)

            if not cmds.objExists(skincluster_new_name):
                skincluster_new_name = cmds.skinCluster(
                    target_mesh,
                    src_skin_influences[source_skincluster],
                    bindMethod=0,
                    toSelectedBones=True,
                    multi=True,
                    name=skincluster_new_name
                )[0]

            # Copy skin weights from the source to the target skin cluster
            cmds.copySkinWeights(
                sourceSkin=source_skincluster,
                destinationSkin=skincluster_new_name,
                noMirror=True,
                influenceAssociation=['label', 'name', 'oneToOne']
            )

        for idx, source_skincluster in enumerate(skin_clusters):
            # Retrieve the previously stored connection map
            connection_map = src_connection_maps[f'{source_skincluster}_MAP']

            # Reconnect the matrix multiplies for the source skin cluster
            self.connect_matrix_mults(connection_map=connection_map, skincluster_name=source_skincluster)

            # Modify the connection map for the target mesh and connect it
            new_connection_map = self.replace_keys_and_values_in_nested_dict(connection_map, source_mesh, target_mesh)
            self.connect_matrix_mults(connection_map=new_connection_map, skincluster_name=target_skinclusters[idx], debug=False)

    def get_skinclusters_on_mesh(self, mesh):
        skin_clusters=[]

        for skin_cluster in cmds.ls(type='skinCluster'):
            geoms = cmds.skinCluster(skin_cluster, q=True, geometry=True)
            if not geoms: continue
            '''
            Finding the skincluster associated with the mesh

            We really only care about things that end in Shape

            Because the skincluster geometry query only returns shape names, we need to check if
            the geometry in the skincluster ends in Shape. If this is true, any partial naming matches
            get culled out and you can focus on only meshes.
            '''
            # makes sure that string eyebrows_mesh is in the skincluster, and also ends with meshShape 
            if mesh in geoms[0] and geoms[0].endswith('Shape'):
                skin_clusters.append(skin_cluster)
        return skin_clusters

    def replace_keys_and_values_in_nested_dict(self, dictionary, source_name, target_name):
        """Recursively replace occurrences of source_name with target_name in all string keys and values."""
        new_dict = {}
        for key, value in dictionary.items():
            # Replace in the key if it's a string
            new_key = key.replace(source_name, target_name) if isinstance(key, str) else key

            # If value is a dictionary, recurse
            if isinstance(value, dict):
                new_value = self.replace_keys_and_values_in_nested_dict(value, source_name, target_name)
            # Replace in the value if it's a string
            elif isinstance(value, str):
                new_value = value.replace(source_name, target_name)
            else:
                new_value = value

            # Assign the modified key and value to the new dictionary
            new_dict[new_key] = new_value

        return new_dict

    def get_compound_attr_connect_map(self, node, compound_attr):
        """
        Lists all connections for a given compound attribute on a node and returns them in a dictionary.
        Args:
        - node (str): The name of the node (e.g., a skinCluster).
        - compound_attr (str): The name of the compound attribute (e.g., "matrix").
        Returns:
        - dict: A dictionary containing the connections.
        """
        # Dictionary to store the connections
        matrix_connections_dict = {}
        joint_connections_dict = {}
        # Get the full path of the compound attribute (node + compound attribute)
        full_attr = f"{node}.{compound_attr}"
        # Check if the attribute exists and is compound
        if not cmds.attributeQuery(compound_attr, node=node, exists=True):
            raise ValueError(f"The attribute {compound_attr} does not exist on node {node}.")
        if not cmds.attributeQuery(compound_attr, node=node, multi=True):
            raise ValueError(f"The attribute {compound_attr} is not a compound array.")
        # Get all indices for the compound array
        indices = cmds.getAttr(full_attr, multiIndices=True)
        # Loop through all indices and find incoming connections
        for index in indices:
            # Build the indexed attribute (e.g., skinCluster.matrix[0])
            indexed_attr = f"{full_attr}[{index}]"
            connection = cmds.listConnections(indexed_attr, source=True, destination=False, plugs=True)[0]
            mult_matrix_input0 = connection.split(".")[0]
            mult_matrix_input0= f'{mult_matrix_input0}.matrixIn[0]'
            if not cmds.objExists(mult_matrix_input0): continue
            mult_matrix_input0_connection = cmds.listConnections(mult_matrix_input0, source=True, destination=False, plugs=True)[0]
            mult_matrix_input0_connection = f'{mult_matrix_input0_connection}[0]'
            if connection:
                # Store connections in the dictionary
                matrix_connections_dict[connection] = indexed_attr
                joint_connections_dict[mult_matrix_input0_connection] = indexed_attr
            else:
                matrix_connections_dict[connection] = None
                joint_connections_dict[mult_matrix_input0_connection] = None

        export_dict = {f'{node}_MATRIX_MULT':matrix_connections_dict,
                    f'{node}_ENV':joint_connections_dict}
        return export_dict

    def connect_skins(self, connection_map, skincluster_name, dict_suffix, debug=False):
        """
        Needs to save out a connection map to keep track of what all the connections originally were.
        CANNOT lose track of which connection goes to which index, this would permanently break the rig!
        If a mismatch does happen there would be a lot of trial and error to figure out which joint goes to which skincluster.matrix[index]

        Args:
        - connection_map (dict) - the
        "teshi_base_body_geo_bodyMechanics_skinCluster_MATRIX_MULT": {"M_neckHead00Localized_multMatrix.matrixSum": "matrix[0]"}
        """
        for key in connection_map:
            if f'{skincluster_name}{dict_suffix}' in key:
                connection_dict = connection_map[key]
                for key in connection_dict:
                    cmds.connectAttr(key, connection_dict[key], force=True)
                    if debug:
                        print(f'{key} was connected to {connection_dict[key]}')

    def connect_skin_joints(self, connection_map, skincluster_name):
        self.connect_skins(connection_map, skincluster_name, dict_suffix="_ENV")

    def connect_matrix_mults(self, connection_map, skincluster_name, debug=False):
        self.connect_skins(connection_map, skincluster_name, dict_suffix="_MATRIX_MULT", debug=debug)

##################################### SmartCopySkins Usage #########################################
SmartCopySkins(source_mesh='jsh_base_cloth_top_fabric_mesh',
                target_mesh='jsh_base_cloth_top_fabric_low_mesh',
                skin_clusters='jsh_base_cloth_top_fabric_mesh_bodyMechanics_skinCluster')
SmartCopySkins(source_mesh='jsh_base_cloth_pants_fabric_mesh',
                target_mesh='jsh_base_cloth_pants_fabric_low_mesh',
                skin_clusters='jsh_base_cloth_pants_fabric_mesh_bodyMechanics_skinCluster')
####################################################################################################