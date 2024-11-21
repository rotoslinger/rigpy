import json, math, os
from importlib import reload

from maya import cmds, mel

from rigbdp.build import rig_hier
from rig.propcmds import stdavars
from rig.propcmds.OLD_components import prop_singleton
from rig_2.tag import utils as tag_utils
from rig.propcmds import prop_base

MODULES = [prop_base, rig_hier, stdavars, prop_singleton, tag_utils]
for mod in MODULES:
    reload(mod)




class PropWeights:
    def __init__(self, geometry_joint_dict):
        '''
        {'geom_name_01':['bone1', 'bone2', 'bone3'],
         'geom_name_01':['boneA', 'boneB', 'boneC'],}
        '''
        self.geometry_joint_dict = geometry_joint_dict

    def create_skinclusters(self):
        ...
    def export_weights(self):
        ...
    def import_weights(self):
        ...



class PropBuild(object):
    def __init__(self,
                 name='allyBook',
                 version=1,
                 props_path=r'C:\Users\harri\Documents\BDP\props',
                 model_file='allyBook_base_model_h_v004.mb',
                 rig_geo_files='',
                 output_path='',
                 radius=None,
                 ):
        self.name = name
        self.props_path = props_path
        self.model_file = model_file
        self.rig_geo_file = rig_geo_files
        self.version = version
        self.radius = radius
        sep = os.path.sep
        self.full_model_path = os.path.normpath(f'{props_path}{sep}{name}{sep}{model_file}')
        if rig_geo_files:
            self.rig_geo_file = os.path.normpath(f'{props_path}{sep}{name}{sep}{rig_geo_files}')
        if not output_path:
            self.out_file=f'{self.name}_base_rig_h_v{version:03}'
            self.output_path = os.path.normpath(f'{props_path}{sep}{name}{sep}{self.out_file}')

        self.__create()

    def __create(self):
        self.__create_std_root()
        self.build_it()
        if self.output_path:
            # If build output path given, save file
            cmds.file(rename=self.output_path)
            cmds.file(save=True, type='mayaBinary')

    def __create_std_root(self):
        self.rig_root = rig_hier.create_rig_hier(name=self.name, 
                                            model_path=self.full_model_path,
                                            rig_geo_path=self.rig_geo_file
                                            )
        if not self.radius:
            rad = self.get_scene_bounds()
            self.radius=rad
        self.std_avars = stdavars.create_stdavar_ctrl(side = "C",
                                                skel_parent = self.rig_root.skeleton_grp,
                                                rig_parent = self.rig_root.rig_grp,
                                                ctrl_sizes = [self.radius,
                                                              ((self.radius)*.9),
                                                              ((self.radius)*.8)],
                                                colors = [ 
                                                            (.8, 0, 0.0),
                                                            (0.4, 0, 0.0),
                                                            (0.4, 0, 0.0)],
                                                ctrl_names = ["World", "Layout", "Root"],
                                                ctrls_with_bones = [False, False, True],
                                                create_buffer_shape = True,
                                                debug = True)
    
    def build_it(self):
        ...

    def get_scene_bounds(self):

        # mel.eval("cleanUpScene 3")

        geometry = cmds.ls(geometry=True)
        cmds.delete(geometry, ch=True)
        geometry = cmds.ls(geometry=True)

        bbox = cmds.exactWorldBoundingBox(geometry)
        min_x, min_y, min_z, max_x, max_y, max_z = bbox

        width = max_x - min_x
        height = max_y - min_y
        depth = max_z - min_z

        radius = math.sqrt((width * 0.5)**2 + (height * 0.5)**2 + (depth * 0.5)**2)
        return radius

    def export_guides(self, output_path=''):
        ''
        buffers = tag_utils.get_all_with_tag('BUFFER')
        control_shapes = tag_utils.get_all_with_tag('CONTROL_SHAPE')
        position_dict = {'xforms':{}, 'points':{}}

        for buffer in buffers:
            position_dict['xforms'][buffer] = cmds.xform(buffer, q=True, matrix=True)
        for shape in control_shapes:
            position_dict['points'][shape] = self.point_positions(shape)

    def point_positions(self, shape):
        points = cmds.ls(f'{shape}.cv[*]', flatten=True)
        point_dict = {}
        for point in points:
            point_dict[point] = cmds.xform(point, q=True, translation=True)
        print(point_dict)
        return point_dict


class AllyBook(PropBuild):
    """Class representing a dog, inheriting from Animal."""
    def __init__(self,
                 name='allyBook',
                 version=1,
                 props_path=r'C:\Users\harri\Documents\BDP\props',
                 model_file='allyBook_base_model_h_v004.mb',
                 rig_geo_file='',
                 build_output_path='',
                 *args, **kwargs):
        # Call the parent class constructor
        super().__init__(*args, **kwargs)

    def build_it(self):
        print('I AM BUILDING')


prop_build = AllyBook()
