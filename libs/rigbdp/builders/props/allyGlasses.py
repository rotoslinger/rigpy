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
class AllyGlasses(prop.PropBuild):
    def __init__(self,
                 name='allyGlasses',
                 version=1,
                 props_path=r'C:\Users\harri\Documents\BDP\props',
                 model_file='allyGlasses_base_model_h_v002.mb',
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
                                        ctrl_sizes = [1,1,1,1,1],
                                        colors = [(1, 1, 0),(0, 1, 0)],
                                        ctrl_names = ["glasses_base", "glasses_bridge"],
                                        # associated_geos = ["glasses_base", "glasses_bridge"],
                                        chained_pos_offset=(0, 0 ,0),
                                        root_pos_offset=(0,-1,0),
                                        debug = True)
        counter = 1 

        prop_base.simple_component(side = "L",
                                    parent_hook = glasses.ctrls[1],
                                    rig_parent = self.rig_root.rig_grp,
                                    ctrl_sizes = [1],
                                    ctrl_names = ["arm"],
                                    create_joints = True,
                                    root_pos_offset=(1,0,0),

                                    create_buffer_shape = True,
                                    joint_parent=glasses.joints[0],
                                    colors = [(1, 0, 0)],

                                    debug = True)
        prop_base.simple_component(side = "R",
                                    parent_hook = glasses.ctrls[1],
                                    rig_parent = self.rig_root.rig_grp,
                                    ctrl_sizes = [1],
                                    ctrl_names = ["arm"],
                                    colors = [(0, 0, 1)],

                                    root_pos_offset=(-1,0,0),

                                    create_joints = True,
                                    create_buffer_shape = True,
                                    joint_parent=glasses.joints[0],

                                    debug = True)
prop_rig = AllyGlasses()
prop_rig.extract_class_info()
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
