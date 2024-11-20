from importlib import reload
from rig_2.tag import utils as tag_utils
from rigbdp.build import misc
from maya import cmds

MODULES = [tag_utils, misc,]
for mod in MODULES:
    reload(mod)

class create_rig_hier():
    def __init__(self,
                 name = "character",
                 model_root='',
                 model_filepath='',

                 rig_geo_filepaths=[]):
        """
        type  name:                string
        param name:                character name
        """
        #---args
        self.name = name

        #---vars
        self.groups = []
        self.model_filepath = model_filepath
        self.rig_geo_filepaths = rig_geo_filepaths
        self.model_root = model_root

        self.__create()


    def __import_maya_file(self):
        if not self.model_filepath: return
        # 1. Create a new scene
    
        model = self.__clean_import_file(self.model_filepath)
        cmds.parent(model, self.geo_grp)
        new_objects = []
        for path in self.rig_geo_filepaths:
            new_objects += self.__clean_import_file(path)
        cmds.parent(new_objects, self.rig_grp)
        
    def __clean_import_file(self, filepath):
        initial_objects = set(cmds.ls(dag=True, shapes=False))

        cmds.file(filepath, i=True, namespace=":")

        # Flatten namespaces (remove them)
        cmds.namespace(set=':')
        namespaces = cmds.namespaceInfo(listOnlyNamespaces=True)
        for ns in namespaces:
            if ns not in ['UI', 'shared']:
                cmds.namespace(force=True, moveNamespace=(ns, ':'))
                cmds.namespace(removeNamespace=ns)
        new_objects = set(cmds.ls(dag=True, shapes=False))
        # Determine what was added
        imported_objects = new_objects - initial_objects
        imported_objects = list(imported_objects)
        if imported_objects and type(imported_objects[0]) == list: 
            imported_objects = imported_objects[0]

        print('IMPORTED OBJECTS : ', imported_objects)
        return imported_objects



    def __create_nodes(self):
        "Create and name rig transforms"
        self.root_grp= cmds.createNode("transform",
                                        name = "c_" +
                                        self.name +
                                        "_grp")

        self.geo_grp = cmds.createNode("transform",
                                        name   = "c_geo_grp",
                                        parent = self.root_grp)

        self.skeleton_grp = cmds.createNode("transform",
                                            name   = "c_skeleton_grp",
                                            parent = self.root_grp)
        self.skel_bind = cmds.createNode("transform",
                                             name   = "c_skelbind_grp",
                                             parent = self.skeleton_grp)
        self.skel_helper = cmds.createNode("transform",
                                                name   = "c_skelhelp_grp",
                                                parent = self.skeleton_grp)

        self.rig_grp = cmds.createNode("transform",
                                       name   = "c_rig_grp",
                                       parent = self.root_grp)

        self.rig_ctrl_grp = cmds.createNode("transform",
                                    name   = "c_rigctrl_grp",
                                    parent = self.rig_grp)
        self.rig_sizectrl_grp = cmds.createNode("transform",
                                    name   = "c_ctrlsize_grp",
                                    parent = self.rig_ctrl_grp)


        self.maintenence_grp = cmds.createNode("transform",
                                                name   = "c_maintenance_grp",
                                                parent = self.root_grp)




        self.control_grp = cmds.createNode("transform",
                                            name   = "c_control_grp",
                                            parent = self.root_grp)

        self.groups = [self.root_grp, self.geo_grp, self.skeleton_grp, self.rig_grp, self.control_grp]
        tag_utils.tag_root_group(self.root_grp)
        tag_utils.tag_rig_group(self.rig_grp)
        tag_utils.tag_rig_ctrl_group(self.rig_ctrl_grp)
        tag_utils.tag_rig_ctrlsize_group(self.rig_sizectrl_grp)
        tag_utils.tag_ctrl_group(self.control_grp)
        tag_utils.tag_geo_group(self.geo_grp)
        tag_utils.tag_skeleton_group(self.skeleton_grp)
        tag_utils.tag_bindjnt_group(self.skel_bind)
        tag_utils.tag_helpjnt_group(self.skel_helper)
        tag_utils.tag_maintenance_group(self.maintenence_grp)

        # Any rig fitting or rig maintenance attributes will go here
        # This will make cleaning up the rig much easier.
        cmds.addAttr(self.maintenence_grp, ln = "fit_ctrl_vis", at = "bool")
        self.fit_ctrl_vis = self.maintenence_grp + ".fit_ctrl_vis"
        cmds.setAttr(self.fit_ctrl_vis, cb = True, e=True)
        cmds.addAttr(self.maintenence_grp, ln = "size_cluster_vis", at = "bool")
        self.size_cluster_vis = self.maintenence_grp + ".size_cluster_vis"
        cmds.setAttr(self.size_cluster_vis, cb = True, e=True)

        cmds.addAttr(self.maintenence_grp, ln = "ctrl_shape_vis", at = "bool", dv=True)
        self.ctrl_shape_vis = self.maintenence_grp + ".ctrl_shape_vis"
        cmds.setAttr(self.ctrl_shape_vis, cb = True, e=True)

        # addAttr -ln "vis_fit_ctrl"  -at bool  |c_Template_grp|c_maintenance_grp;
        # setAttr -e-channelBox true |c_Template_grp|c_maintenance_grp.vis_fit_ctrl;

    def finalize_maintenence(self):
        # meant to be used after the entire rig has finished building
        # creates all neccesary attributes.
        self.groups = [self.root_grp, self.geo_grp, self.skeleton_grp, self.rig_grp, self.control_grp, self.maintenence_grp]

        # wires up the maintenence group
        # turns on drawing overrides
        # Adds visibility switches for the rig groups
        # Adds override display types for each rig group

        # cmds.setAttr(self.groups[i]+".overrideEnabled",
        #         keyable = False, 
        #         channelBox = True,)

        pass

    def __lock_attrs(self):
        "Lock out attributes"
        for i in range(len(self.groups)):
            #---lock transform
            misc.lock_attrs(node = self.groups[i])
            #---make vis non keyable
            cmds.setAttr(self.groups[i]+".v",
                         keyable = False,
                         channelBox = True)
            cmds.setAttr(self.groups[i]+".overrideEnabled",
                         keyable = False,
                         channelBox = True,)


            #---expose needed attrs
            cmds.setAttr(self.groups[i]+".overrideDisplayType",
                         2,
                         keyable = False,
                         channelBox = True,)
            cmds.setAttr(self.groups[i]+".ihi", 0)

    def __create(self):
        "Put it all together"
        cmds.file(new=True, force=True)

        self.__create_nodes()

        self.__lock_attrs()
        self.__import_maya_file()
