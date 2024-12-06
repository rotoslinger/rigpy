from importlib import reload
import inspect
from rigbdp.build.components import rig_hier
from rig.propcmds import stdavars
from rig.propcmds.OLD_components import prop_singleton
from rig_2.tag import utils as tag_utils
from rigbdp.build.components import prop_base
from rigbdp.build import prop
MODULES = [prop_base, rig_hier, stdavars, prop_singleton, tag_utils, prop]
for mod in MODULES:
    reload(mod)
    
class subDocu(prop.PropBuild):
    def __init__(self,
                 name='subDocu',
                 version=1,
                 props_path=r'C:\Users\harri\Documents\BDP\props',
                 model_file='subDocu_base_model_h_v001.mb',
                 rig_geo_files='',
                 output_path='',
                 radius='',
                 guide_vis=True,
                 ctrl_vis=False,
                 *args, **kwargs):
        # Call the parent class constructor
        super().__init__(name=name,
                         version=version,
                         props_path=props_path,
                         model_file=model_file,
                         rig_geo_files=rig_geo_files,
                         output_path=output_path,
                         radius=radius,
                         guide_vis=guide_vis,
                         ctrl_vis=ctrl_vis,
                         *args, **kwargs)

    def build_it(self):

        glasses = prop_base.simple_component(side = "",
                                        parent_hook = self.std_avars.root_ctrl,
                                        rig_parent = self.rig_root.rig_grp,
                                        ctrl_sizes = [8,8],
                                        colors = [(1, 1, 0),(0, 1, 0)],
                                        ctrl_names = ["glasses_base", "glasses_bridge"],
                                        create_joints = True,
                                        create_buffer_shape = True,
                                        chained_pos_offset=(0, 0 ,0),

                                        debug = True)
        counter = 1 

        prop_base.simple_component(side = "L",
                                    parent_hook = glasses.ctrls[1],
                                    rig_parent = self.rig_root.rig_grp,
                                    ctrl_sizes = [2],
                                    ctrl_names = ["arm"],
                                    create_joints = True,
                                    create_buffer_shape = True,
                                    joint_parent=glasses.joints[0],
                                    colors = [(1, 0, 0)],

                                    debug = True)
        prop_base.simple_component(side = "R",
                                    parent_hook = glasses.ctrls[1],
                                    rig_parent = self.rig_root.rig_grp,
                                    ctrl_sizes = [2],
                                    ctrl_names = ["arm"],
                                    colors = [(0, 0, 1)],
                                    create_joints = True,
                                    create_buffer_shape = True,
                                    joint_parent=glasses.joints[0],

                                    debug = True)


prop_rig = subDocu()

# attempt to export guides, just in case you have forgotten to.
# this will probably bite us but whatever
# prop_rig.export_prop_build()
prop_rig.create()

prop_rig.import_prop_build()

# prop_rig.skincluster_on_off(on=False)

prop_rig.guides_world_space()
# prop_rig.guides_world_space(world_space=False)

prop_rig.set_maintenance_defaults()
prop_rig.finalize()




# def create_std_rig(name = "subDocu_base_rig_h_v001"):
#     rig_root = rig_hier.create_rig_hier(name=name, 
#                                         model_path=r'C:\Users\harri\Documents\BDP\props\subDocu\subDocu_base_model_h_v001.mb',
#                                         rig_geo_path=[r'C:\Users\harri\Documents\BDP\props\subDocu\hose_patch.mb'])
#     std_avars = stdavars.create_stdavar_ctrl(side = "C",
#                                             skel_parent = rig_root.skeleton_grp,
#                                             rig_parent = rig_root.rig_grp,
#                                             ctrl_sizes = [12,((12)*.9),((11)*.9)],
#                                             colors = [ 
#                                                         (.8, 0, 0.0),
#                                                         (0.4, 0, 0.0),
#                                                         (0.4, 0, 0.0)],
#                                             ctrl_names = ["World", "Layout", "Root"],
#                                             ctrls_with_bones = [False, False, True],
#                                             create_buffer_shape = True,
#                                             debug = True)
#     glasses = prop_base.simple_component(side = "",
#                                     parent_hook = std_avars.root_ctrl,
#                                     rig_parent = rig_root.rig_grp,
#                                     ctrl_sizes = [8,8],
#                                     colors = [(1, 1, 0),(0, 1, 0)],
#                                     ctrl_names = ["glasses_base", "glasses_bridge"],
#                                     create_joints = True,
#                                     create_buffer_shape = True,
#                                     chained_pos_offset=(0, 0 ,0),

#                                     debug = True)
#     counter = 1 

#     prop_base.simple_component(side = "L",
#                                 parent_hook = glasses.ctrls[1],
#                                 rig_parent = rig_root.rig_grp,
#                                 ctrl_sizes = [2],
#                                 ctrl_names = ["arm"],
#                                 create_joints = True,
#                                 create_buffer_shape = True,
#                                 joint_parent=glasses.joints[0],
#                                 colors = [(1, 0, 0)],

#                                 debug = True)
#     prop_base.simple_component(side = "R",
#                                 parent_hook = glasses.ctrls[1],
#                                 rig_parent = rig_root.rig_grp,
#                                 ctrl_sizes = [2],
#                                 ctrl_names = ["arm"],
#                                 colors = [(0, 0, 1)],
#                                 create_joints = True,
#                                 create_buffer_shape = True,
#                                 joint_parent=glasses.joints[0],

#                                 debug = True)


# create_std_rig()
