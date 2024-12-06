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

class AllyBookmark(prop.PropBuild):
    def __init__(self,
                 name='allyBookmark',
                 version=1,
                 props_path=r'C:\Users\harri\Documents\BDP\props',
                 model_file='allyBookmark_base_model_h_v004.mb',
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
        l_page = prop_base.simple_component(side = 'C',
                                        parent_hook = self.std_avars.root_ctrl,
                                        rig_parent = self.rig_root.rig_grp,
                                        ctrl_sizes = [1, 1, 1],
                                        colors = [(1, 1, 0),(0, 1, 0)],
                                        ctrl_names = ['L_Page',
                                                      'L_Mountain',
                                                      'R_Mountain',
                                                      'R_Tree00',
                                                      'R_Tree01'],
                                        associated_geos=[[], 
                                                         ],
                                        chained_pos_offset=(0, 0 ,0),
                                        debug = True)
        counter = 1 
prop_rig = AllyBookmark()

# attempt to export guides, just in case you have forgotten to.
# this will probably bite us but whatever
prop_rig.export_prop_build()

prop_rig.create()
prop_rig.import_prop_build()

# prop_rig.skincluster_on_off(on=False)

prop_rig.guides_world_space()
prop_rig.guides_world_space(world_space=False)

prop_rig.set_maintenance_defaults()
# prop_rig.finalize()
