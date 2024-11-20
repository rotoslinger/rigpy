



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