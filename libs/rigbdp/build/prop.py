import json, math, os
from importlib import reload

from maya import cmds, mel

from rigbdp.build.components import rig_hier
from rig.propcmds import stdavars
from rig.propcmds.OLD_components import prop_singleton
from rigbdp.import_export import file
from rig_2.tag import utils as tag_utils
from rig.propcmds import prop_base
from rigbdp.build import build_pathing

MODULES = [prop_base, rig_hier, stdavars, prop_singleton, tag_utils, file, build_pathing]
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
                 name,
                 version,
                 props_path,
                 model_file,
                 rig_geo_files,
                 output_path,
                 radius,
                 root_geometry='',
                 guide_vis=False,
                 ctrl_vis=True,
                 *args, **kwargs
                 ):
        self.name = name
        self.props_path = props_path
        self.model_file = model_file
        self.rig_geo_file = rig_geo_files
        self.version = version
        self.radius = radius
        self.root_geometry = root_geometry
        self.guide_vis = guide_vis
        self.ctrl_vis = ctrl_vis
        sep = os.path.sep
        self.guide_path = ''
        self.full_model_path = os.path.normpath(f'{props_path}{sep}{name}{sep}{model_file}')
        if rig_geo_files:
            self.rig_geo_file = os.path.normpath(f'{props_path}{sep}{name}{sep}{rig_geo_files}')
        if not output_path:
            self.output_path = f'{props_path}{sep}{name}'
            out_file = f'{self.name}_base_rig_h_v{version:03}'
            self.out_file = os.path.normpath(f'{self.output_path}{sep}{out_file}')
        self.guide_path = f'{self.output_path}{sep}{self.name}_GUIDES.json'
        self.weights_path = f'{self.output_path}{sep}weights{sep}'

    def create(self):
        self.__create_std_root()
        self.build_it()
        if self.output_path:
            # If build output path given, save file
            cmds.file(rename=self.out_file)
            cmds.file(save=True, type='mayaBinary')
        self.set_maintenance_defaults()

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
                                                associated_geos = ['','', self.root_geometry],
                                                ctrls_with_bones = [False, False, True],
                                                create_buffer_shape = True,
                                                debug = True)
    
    def build_it(self):
        ...

    def remove_unknown_plugins(self):
       mel.eval('''
                string $plugin;
                string $unknownPlugins[] = `unknownPlugin -query -list`;
                for ($plugin in $unknownPlugins)
                {
                unknownPlugin -remove $plugin;
                };''')
        
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


    def guides_world_space(self, world_space=True):
        '''
        world_space True: guides move independently
        world_space False: buffers inherit their parent's rotation/translation
        '''
        if world_space:
            self.guides_to_world_space()
        else:
            self.guides_to_parent_space()

    def guides_to_world_space(self):
        self.guide_space_switch(0)

    def guides_to_parent_space(self):
        self.guide_space_switch(1)

    def guide_space_switch(self, space=0):
        '''
        space must be 0 or 1.
        0 is world space (buffers move independently)
        1 is parent space (buffers inherit their parent's rotation/translation)
        '''
        position_dict = self.get_guide_positions()
        buffers = tag_utils.get_all_with_tag('BUFFER')
        for buffer in buffers:
            cmds.setAttr(f'{buffer}.inheritsTransform', space)
        self.set_guide_positions(position_dict)

    def get_guide_positions(self):
        buffers = tag_utils.get_all_with_tag('BUFFER')
        r_dict = {}

        for buffer in buffers:
            r_dict[buffer] = cmds.xform(buffer, q=True,
                                        matrix=True,
                                        worldSpace=True)
        return r_dict

    def set_guide_positions(self, position_dict):
        for buffer in position_dict:
            position_dict[buffer] = cmds.xform(buffer, matrix=position_dict[buffer],
                                               worldSpace=True)

    def export_prop_build(self, output_path=''):
        if not output_path:
            output_path = self.guide_path

        buffers = tag_utils.get_all_with_tag('BUFFER')
        control_shapes = tag_utils.get_all_with_tag('CONTROL_SHAPE')

        '''
        xforms dict {buffer_name: 16_digit_matrix}
        points dict {shape_name:{point_name.cv[0]: 3_digit_position}}
        skinclusters dict {geometry_name:{skincluster_name:name,
                                         influences:[list_of_influences],
                                         export_paths:[paths]}}
        '''

        self.position_dict = {'xforms':{}, 'points':{}, 'skinclusters':{}}

        for buffer in buffers:
            self.position_dict['xforms'][buffer] = cmds.xform(buffer, q=True,
                                                              matrix=True,
                                                              worldSpace=True)
        for shape in control_shapes:
            self.position_dict['points'][shape] = self.get_point_positions(shape)

        file.backup_file_simple(output_path)
        with open(output_path, 'w') as json_file:
            json.dump(self.position_dict, json_file, indent=4)

        print(f'Guides exported to: {output_path}')

    def get_skincluster_data(self):
        '''
        gets all of the skincluster data needed for the export
        prepare the skincluster (cleans up naming if needed, names based on geo name)
        finds all export paths
        exports the skinclusters with skincluster
        '''
        # Specify the weight file path
        self.weights_path
        all_skinclusters=cmds.ls(type='skinCluster')

        '''
        skinclusters_dict {geometry_name:{skincluster_name:name,
                                          influences:[list_of_influences],
                                          export_path:''}}
        '''
        skincluster_dict = {}

        for skincluster in all_skinclusters:
            geo_name = cmds.skinCluster(skincluster, query=True, geometry=True)
            geo_formatted_name = f'{self.weights_path}{geo_name}_skinCluster'
            if not skincluster == geo_formatted_name:
                skincluster = cmds.rename(skincluster, geo_formatted_name)
            influences = cmds.skinCluster(skincluster, query=True, influence=True)
            export_path = f'{self.weights_path}{geo_formatted_name}.json'
            cmds.deformerWeights(export_path,
                                 export = True,
                                 deformer=skincluster,
                                 path = export_path)
            skincluster_dict[geo_name]={'skincluster_name':skincluster}
        # Specify the deformer and geometry
        deformer = 'skinCluster1'
        geometry = 'pSphere1'
        

    def import_prop_build(self, input_path=''):
        if not input_path:
            input_path = self.guide_path
        with open(self.guide_path, 'r') as json_file:
            self.position_dict = json.load(json_file)
        print(f'Guides imported from: {input_path}')

        for buffer in self.position_dict['xforms']:
            # print(f"buffer {buffer}, position {self.position_dict['xforms'][buffer]}")
            cmds.xform(buffer,
                       matrix=self.position_dict['xforms'][buffer],
                       worldSpace=True)
            
        for shape in self.position_dict['points']:
            # for point in self.position_dict['points'][shape]:
                # print(f"shape {shape}, point {point}, position {self.position_dict['points'][shape][point]}")
            self.set_point_positions(point_position_data = self.position_dict['points'][shape])

    def get_point_positions(self, shape):
        points = cmds.ls(f'{shape}.cv[*]', flatten=True)
        point_dict = {}

        for point in points:
            point_dict[point] = cmds.xform(point, q=True, translation=True, objectSpace=True)
        return point_dict
    
    def set_point_positions(self, point_position_data):
        for point in point_position_data:
            # print(f"point {point}, position {point_position_data[point]}")
            cmds.xform(point, translation=point_position_data[point], objectSpace=True)

    def set_maintenance_defaults(self):
        maintenance = tag_utils.get_all_with_tag('MAINTENANCE_GRP')
        if maintenance:maintenance=maintenance[0]
        else:return
        cmds.setAttr(f'{maintenance}.ctrl_shape_vis', self.ctrl_vis)
        cmds.setAttr(f'{maintenance}.fit_ctrl_vis', self.guide_vis)

    def finalize(self):
        maintenance = tag_utils.get_all_with_tag('MAINTENANCE_GRP')
        if maintenance:maintenance=maintenance[0]
        else:return
        cmds.setAttr(f'{maintenance}.ctrl_shape_vis', True)
        cmds.setAttr(f'{maintenance}.fit_ctrl_vis', False)





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


