import json, math, os, inspect, types, textwrap
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
        self.dir_to_prop = f'{props_path}{sep}{name}'

        # If you don't have the directories, this will create them.
        build_pathing.create_prop_structure(prop_name=self.name,
                                            dir_to_prop=f'{props_path}{sep}')

        self.full_model_path = os.path.normpath(f'{props_path}{sep}{name}{sep}model{sep}{model_file}')
        if rig_geo_files:
            self.rig_geo_file = os.path.normpath(f'{props_path}{sep}{name}{sep}model{sep}{rig_geo_files}')
        if not output_path:
            self.output_path = f'{props_path}{sep}{name}'
            out_file = f'{self.name}_base_rig_h_v{version:03}'
            self.out_file = os.path.normpath(f'{self.output_path}{sep}{out_file}')
        self.guide_path = f'{self.output_path}{sep}guides{sep}{self.name}_GUIDES.json'
        self.weights_path = f'{self.output_path}{sep}weights'

        # Find find other files needed to build
        found_dirs = build_pathing.return_found_prop_files(prop_name=self.name,
                                                           dir_to_prop=props_path)
        self.weights_files = found_dirs['weights_files']
        self.sdk_file = found_dirs['sdk_file']


    def create(self):
        self.__create_std_root()
        self.build_it()
        if self.output_path:
            # If build output path given, save file
            file.backup_file_simple(f'{self.out_file}.mb')
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

        self.rig_data = {'xforms':{}, 'points':{}, 'skinclusters':{}}

        for buffer in buffers:
            self.rig_data['xforms'][buffer] = cmds.xform(buffer, q=True,
                                                              matrix=True,
                                                              worldSpace=True)
        for shape in control_shapes:
            self.rig_data['points'][shape] = self.get_point_positions(shape)
        
        self.rig_data['skinclusters'] = self.export_skincluster_data()


        file.backup_file_simple(output_path)
        with open(output_path, 'w') as json_file:
            json.dump(self.rig_data, json_file, indent=4)

        print(f'Guides exported to: {output_path}')

    def export_skincluster_data(self):
        '''
        gets all of the skincluster data needed for the export
        prepare the skincluster (cleans up naming if needed, names based on geo name)
        finds all export paths
        exports the skinclusters with skincluster
        '''

        '''
        skinclusters_dict {geometry_name:{skincluster_name:name,
                                          influences:[list_of_influences],
                                          export_path:''}}
        '''
        self.skincluster_dict = {}


        for skincluster in cmds.ls(type='skinCluster'):
            # find important about all the skinclusters in the scene
            geo_name = cmds.skinCluster(skincluster, query=True, geometry=True)[0]
            skincluster_name = f'{geo_name}_skinCluster'
            if not skincluster == skincluster_name:
                skincluster = cmds.rename(skincluster, skincluster_name)
            influences = cmds.skinCluster(skincluster, query=True, influence=True)
            export_name = f'{skincluster_name}.json'
            mayaified_path = build_pathing.mayaify_path(self.weights_path)
            # export_path = f'{mayaified_path}{skincluster_name}.json'

            self.skincluster_dict[geo_name]={'skincluster_name':skincluster,
                                             'influences':influences,
                                             'filename':export_name,
                                             'deformer':skincluster_name,
                                             'path':mayaified_path,
                                             }

            cmds.deformerWeights(export_name,
                        export = True,
                        deformer=skincluster_name,
                        method = "index",
                        path = mayaified_path)

        return self.skincluster_dict
        # Specify the deformer and geometry
    def make_skinclusters(self):
        '''
        using the skincluster dictionary
        '''
        skincluster_data = self.rig_data['skinclusters']
        if not skincluster_data: return
        for geometry in skincluster_data:
            data = skincluster_data[geometry]
            skincluster_name = data['skincluster_name']
            influences = data['influences']
            path = data['path']
            filename = data['filename']
            deformer = data['deformer']
            if not cmds.objExists(skincluster_name):
                print('influences ', influences)                                    
                print('geometry ', geometry)                                    


                skincluster_name = cmds.skinCluster(influences, geometry, name=skincluster_name,
                                                    toSelectedBones=True, bindMethod=0,
                                                    skinMethod=0, normalizeWeights=1)
            # path, filename = os.path.split(path)

            # print('filename ', filename)
            # print('skincluster_name ', skincluster_name)
            # print('path ', path)
            # "filename": "allyBook_base_mountain_paper_subShape_skinCluster.json",
            # "deformer": "allyBook_base_mountain_paper_subShape_skinCluster",
            # "path": "C:/Users/harri/Documents/BDP/props/allyBook/weights"

            cmds.deformerWeights(filename,
                             im = True,
                             method = "index",
                             deformer=deformer,
                             path = path)

            cmds.skinCluster(skincluster_name , edit = True, forceNormalizeWeights = True);

            # print(f'geometry: {geometry}')
            # print('skincluster_name', data['skincluster_name'])
            # print('influences', data['influences'])
            # print('export_path', data['export_path'])

    def import_prop_build(self, input_path=''):
        if not input_path:
            input_path = self.guide_path
        with open(self.guide_path, 'r') as json_file:
            self.rig_data = json.load(json_file)
        print(f'Guides imported from: {input_path}')

        for buffer in self.rig_data['xforms']:
            # print(f"buffer {buffer}, position {self.position_dict['xforms'][buffer]}")
            cmds.xform(buffer,
                       matrix=self.rig_data['xforms'][buffer],
                       worldSpace=True)
            
        for shape in self.rig_data['points']:
            # for point in self.position_dict['points'][shape]:
                # print(f"shape {shape}, point {point}, position {self.position_dict['points'][shape][point]}")
            self.set_point_positions(point_position_data = self.rig_data['points'][shape])
        self.make_skinclusters()

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

    def skincluster_on_off(self, on=True):
        for skincluster in cmds.ls(type='skinCluster'):
            cmds.setAttr(f'{skincluster}.envelope', float(on))

    def finalize(self):
        maintenance = tag_utils.get_all_with_tag('MAINTENANCE_GRP')
        if maintenance:maintenance=maintenance[0]
        else:return
        cmds.setAttr(f'{maintenance}.ctrl_shape_vis', True)
        cmds.setAttr(f'{maintenance}.fit_ctrl_vis', False)
        self.guides_world_space(world_space=False)

    def extract_class_info(self):
        """
        Extracts the class definition and instance state for recreation.
        :return: A dictionary with the class definition and state.
        """
        cls = self.__class__

        # Get the class name and its module
        class_name = cls.__name__
        module_name = cls.__module__

        # Get the class-level attributes
        class_attrs = {
            k: v for k, v in cls.__dict__.items()
            if not (k.startswith('__') and k.endswith('__'))  # Exclude built-ins
        }

        # Get the instance attributes (state)
        instance_state = self.__dict__

        # Get all methods (including inherited, excluding built-ins)
        methods = {}
        for name, member in inspect.getmembers(cls):
            if isinstance(member, types.FunctionType) and not name.startswith('__'):  # Exclude built-ins
                try:
                    methods[name] = inspect.getsource(member)
                except OSError:
                    methods[name] = f'# Unable to retrieve source for {name}'

        # Create a reconstruction template using textwrap.dedent
        self.class_string = textwrap.dedent(f"""
        # Module: {module_name}
        class {class_name}:
            # Class attributes
        """)
        
        for attr, value in class_attrs.items():
            self.class_string += f"    {attr} = {repr(value)}\n"

        self.class_string += "\n    # Methods\n"
        for method_code in methods.values():
            self.class_string += f"{method_code}\n\n"  # Add extra newline for separation

        # Format the instance state
        self.class_string += f"\n    # Instance state\n"
        self.class_string += f"    instance = {class_name}.__new__({class_name})\n"
        self.class_string += f"    instance.__dict__.update({repr(instance_state)})\n"

        # Optionally, format the string for better readability (width can be adjusted)
        self.class_string = textwrap.indent(self.class_string, '    ')

        print('class string ', self.class_string)  # Using print for newlines
        return self.class_string
    def create_class_attr(self):
        self.maintenance = tag_utils.get_all_with_tag('MAINTENANCE_GRP')
        if not self.maintenance: return
        self.maintenance = self.maintenance[0]
        cmds.addAttr(self.maintenance, longName='Class', dataType='string')
        self.class_attribute = f'{self.maintenance}.Class'

def recreate_class_from_maya_string(node_name):
    """
    Recreate a class from a string stored in a Maya attribute.
    
    :param node_name: The name of the Maya node containing the class string.
    """
    # Retrieve the class definition string from the Maya attribute
    class_string = cmds.getAttr(f'{node_name}.classInfo')

    # Execute the class definition to create it in the current context
    exec(class_string, globals())

    # Get the class name from the string
    class_name = class_string.split('class ')[1].split(':')[0].strip()

    # Create an instance without calling __init__
    instance = globals()[class_name].__new__(globals()[class_name])

    # Manually update instance state from the extracted string
    instance_state_string = textwrap.dedent(f"""
    instance.__dict__.update({{
        'attribute': 'Initial Value',  # Replace with actual state from Maya
    }})
    """)

    exec(instance_state_string, globals())

    # Now you can use the instance
    instance.display_attribute()  # Assuming display_attribute exists in the class
    # Optionally, call any methods as needed
    instance.update_attribute('Updated Value')  # Assuming update_attribute exists
    instance.display_attribute()  # Output should reflect the updated value



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


