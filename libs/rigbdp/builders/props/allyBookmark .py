from importlib import reload
from rigbdp.build import rig_hier
from rig.propcmds import stdavars
from rig.propcmds.OLD_components import prop_singleton
from rig_2.tag import utils as tag_utils
from rig.propcmds import prop_base

MODULES = [prop_base, rig_hier, stdavars, prop_singleton, tag_utils]
for mod in MODULES:
    reload(mod)


def create_std_rig(name = "allyBookmark"):
    rig_root = rig_hier.create_rig_hier(name=name, 
                                        model_path=r'C:\Users\harri\Documents\BDP\props\allyBook\subDocu_base_model_h_v001.mb'
                                        )
    std_avars = stdavars.create_stdavar_ctrl(side = "C",
                                            skel_parent = rig_root.skeleton_grp,
                                            rig_parent = rig_root.rig_grp,
                                            ctrl_sizes = [12,((12)*.9),((11)*.9)],
                                            colors = [ 
                                                        (.8, 0, 0.0),
                                                        (0.4, 0, 0.0),
                                                        (0.4, 0, 0.0)],
                                            ty_offsets = [0,0,0],
                                            ctrl_names = ["World", "Layout", "Root"],
                                            ctrls_with_bones = [False, False, True],
                                            create_buffer_shape = True,
                                            debug = True)
    child_001 = prop_base.simple_component(side = "",
                                            parent_hook = std_avars.root_ctrl,
                                            skel_parent = rig_root.skeleton_grp,
                                            rig_parent = rig_root.rig_grp,
                                            ctrl_sizes = [8],
                                            colors = [(1, 1, 0.0)],
                                            ty_offsets = [0,0,0],
                                            ctrl_names = ["bend01", "bend02", "bend03"],
                                            create_joints = True,
                                            create_buffer_shape = True,

                                            debug = True)

create_std_rig()
