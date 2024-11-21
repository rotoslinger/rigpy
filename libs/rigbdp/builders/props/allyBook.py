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

class AllyBook(prop.PropBuild):
    def __init__(self, 
                 name='allyBook',
                 version=1,
                 props_path=r'C:\Users\harri\Documents\BDP\props',
                 model_file='allyBook_base_model_h_v004.mb',
                 rig_geo_files='',
                 output_path='',
                 radius='',
                 *args, **kwargs):
        # Pass arguments explicitly to the parent class
        super().__init__(name=name,
                         version=version,
                         props_path=props_path,
                         model_file=model_file,
                         rig_geo_files=rig_geo_files,
                         output_path=output_path,
                         radius=radius,
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
                                        associated_geos=[['allyBook_base_bookPage_paper_sub.f[5857]', 'allyBook_base_bookPage_paper_sub.f[5866]'], 
                                                         ['allyBook_base_mountain_paper_sub.f[2789]', 'allyBook_base_mountain_paper_sub.f[3474]'],
                                                         ['allyBook_base_mountain_paper_sub.f[2844]', 'allyBook_base_mountain_paper_sub.f[3528]'],
                                                         ['allyBook_base_pinetreeSupport_a_paper_sub.f[143]', 'allyBook_base_pinetreeSupport_a_paper_sub.f[167]'],
                                                         ['allyBook_base_pinetree_a_paper_sub.f[1318]', 'allyBook_base_pinetree_a_paper_sub.f[1319]'],
                                                         ],
                                        chained_pos_offset=(0, 0 ,0),
                                        debug = True)
        counter = 1 

        prop_base.simple_component(side = 'L',
                                    parent_hook = l_page.ctrls[1],
                                    rig_parent = self.rig_root.rig_grp,
                                    ctrl_sizes = [1],
                                    ctrl_names = ['Tree00', 'Tree01', ],
                                    associated_geos=['allyBook_base_pinetreeSupport_b_paper_sub',
                                                    'allyBook_base_pinetree_b_paper_sub'],
                                    create_joints = True,
                                    create_buffer_shape = True,
                                    joint_parent=l_page.joints[0],
                                    colors = [(1, 0, 0)],

                                    debug = True)
        sun_base = prop_base.simple_component(side = 'L',
                                    parent_hook = l_page.ctrls[0],
                                    rig_parent = self.rig_root.rig_grp,
                                    ctrl_sizes = [1],
                                    ctrl_names = ['SunBase', 'SunBaseFlap'],
                                    associated_geos=[
                                                     ['polySurface4.f[1442]', 'polySurface4.f[1515]'],
                                                     ['polySurface4.f[438]', 'polySurface4.f[1100]'],
                                                    ],
                                    colors = [(0, 0, 1)],
                                    create_joints = True,
                                    create_buffer_shape = True,
                                    joint_parent=l_page.joints[0],

                                    debug = True)
        sun = prop_base.simple_component(side = 'L',
                                    parent_hook = sun_base.ctrls[0],
                                    associated_geos=[['polySurface9.f[543]', 'polySurface9.f[550]']],
                                    rig_parent = self.rig_root.rig_grp,
                                    ctrl_sizes = [1],
                                    ctrl_names = ['Sun'],
                                    colors = [(0, 0, 1)],
                                    create_joints = True,
                                    create_buffer_shape = True,
                                    joint_parent=l_page.joints[0],

                                    debug = True)


prop_rig = AllyBook()
prop_rig.create()





# def create_std_rig(name = "allyBook_base_model_h"):
#     rig_root = rig_hier.create_rig_hier(name=name, 
#                                         model_path=r'C:\Users\harri\Documents\BDP\props\allyBook\allyBook_base_model_h_v004.mb'
#                                         )
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
#     l_page = prop_base.simple_component(side = "L",
#                                     parent_hook = std_avars.root_ctrl,
#                                     rig_parent = rig_root.rig_grp,
#                                     ctrl_sizes = [8,8],
#                                     colors = [(1, 1, 0),(0, 1, 0)],
#                                     ctrl_names = ["Page"],
#                                     create_joints = True,
#                                     create_buffer_shape = True,
#                                     chained_pos_offset=(0, 0 ,0),

#                                     debug = True)
#     counter = 1 

#     prop_base.simple_component(side = "L",
#                                 parent_hook = l_page.ctrls[0],
#                                 rig_parent = rig_root.rig_grp,
#                                 ctrl_sizes = [2],
#                                 ctrl_names = ["Arm"],
#                                 create_joints = True,
#                                 create_buffer_shape = True,
#                                 joint_parent=l_page.joints[0],
#                                 colors = [(1, 0, 0)],

#                                 debug = True)
#     prop_base.simple_component(side = "r",
#                                 parent_hook = l_page.ctrls[0],
#                                 rig_parent = rig_root.rig_grp,
#                                 ctrl_sizes = [2],
#                                 ctrl_names = ["Arm"],
#                                 colors = [(0, 0, 1)],
#                                 create_joints = True,
#                                 create_buffer_shape = True,
#                                 joint_parent=l_page.joints[0],

#                                 debug = True)


# create_std_rig()
