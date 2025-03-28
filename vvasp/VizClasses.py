from .utils import *
from .io import probe_geometries, preferences, custom_user_mesh_transformations
from .BaseVizClasses import VVASPBaseVisualizerClass, AbstractBaseProbe, ACTIVE_COLOR, INACTIVE_COLOR

class CustomMeshObject(VVASPBaseVisualizerClass):
    """
    This class extends the VVASPBaseVisualizerClass and allows the user to load their own mesh files
    into the pyvista scene. The base class handles the logic for moving the mesh, making it active, etc.

    """
    name = "CustomMeshObject"
    def __init__(self,
                 mesh_paths,
                 vistaplotter,
                 scale_factor=1000.0, # units of pyvista frame are um, but most meshes are in mm
                 pyvista_mesh_args=None, # a list of dicts with keyword arguments for pv.read()
                 mesh_origin=(0,0,0), # change this if the desired rotation point of the mesh is different from the origin of the mesh file
                 mesh_rotation=(0,0,0), # change this to reorient the mesh in the scene if needed
                 starting_position=(0,0,0),
                 starting_angles=(0,0,0),
                 active=True,
                 **kwargs):
        if isinstance(mesh_paths, (str, Path)):
            mesh_paths = [mesh_paths]
        self.mesh_paths = mesh_paths
        self.scale_factor = scale_factor
        self.mesh_origin = mesh_origin
        self.mesh_rotation = mesh_rotation
        super().__init__(vistaplotter, starting_position, starting_angles, active, pyvista_mesh_args, **kwargs)
        

    def create_meshes(self):
        # Your mesh creation logic here
        # TODO: add a way to define transformations
        # TODO: define a new origin for the mesh 
        for p in self.mesh_paths:
            mesh = pv.read(p).scale(self.scale_factor)
            mesh = mesh.translate(self.mesh_origin)
            mesh = mesh.rotate_x(self.mesh_rotation[0])
            mesh = mesh.rotate_y(self.mesh_rotation[1])
            mesh = mesh.rotate_z(self.mesh_rotation[2])
            #rotated_translation = rotation_matrix_from_degrees(*self.mesh_rotation).T @ self.mesh_origin # the translation of the mesh must be rotated into new axes
            #mesh = mesh.translate(rotated_translation)
            self.meshes.append(mesh)
    
class Probe(AbstractBaseProbe):
    name = "Probe"
    def __init__(self,
                 probetype,
                 vistaplotter,
                 starting_position=(0,0,0),
                 starting_angles=(0,0,0),
                 active=True,
                 root_intersection_mesh=None,
                 **kwargs):
        self.name = probetype
        geometry_data = probe_geometries[probetype]
        self.probetype = probetype
        self.shank_offsets_um = geometry_data['shank_offsets_um'] # the offsets of the shanks in um
        self.shank_dims_um = geometry_data['shank_dims_um'] # the dimensions of one shank in um
        super().__init__(vistaplotter, starting_position, starting_angles, active, root_intersection_mesh, **kwargs)
    
    def create_meshes(self):
        for dims, offset in zip(self.shank_dims_um, self.shank_offsets_um):
            shank_vectors = np.array([[dims[0],dims[1],0], #the orthogonal set of vectors used to define a rectangle, these will be translated and rotated about the tip
                                      [dims[0],0,0],
                                      [0,0,dims[2]]])
            vecs = shank_vectors + np.array(offset).T
            self.meshes.append(pv.Rectangle(vecs.astype(np.float32)))

    @property
    def shank_origins(self):
        '''Used for tracking the regions that each shank is in'''
        dims = np.stack(self.shank_dims_um) # shanks by dims
        offsets = np.stack(self.shank_offsets_um)
        offsets[:,0] = offsets[:,0] + dims[:,0] / 2 
        offsets[:,2] = offsets[:,2] + dims[:,2] / 2 
        rotated_offsets = np.dot(offsets, self.rotation_matrix.T)
        return rotated_offsets + self.origin

class NeuropixelsChronicHolder(AbstractBaseProbe):

    # Define mapping of (chassis_type, probetype) to the mesh file and name that gets logged to the experiment file
    mesh_mapping = {
        ('head_fixed', 'NP24'): ('np2_head_fixed.stl', 'NP2 chronic holder - head fixed'),
        ('freely_moving', 'NP24'): ('np2_freely_moving.stl', 'NP2 chronic holder - freely moving'),
        ('head_fixed', 'NP24a'): ('np2a_head_fixed.stl', 'NP2a chronic holder - head fixed'),
        ('freely_moving', 'NP24a'): ('np2a_freely_moving.stl', 'NP2a chronic holder - freely moving'),
        ('head_fixed', 'NP1'): ('np1_head_fixed.stl', 'NP1 chronic holder - head fixed'),
        ('freely_moving', 'NP1'): ('np1_freely_moving.stl', 'NP1 chronic holder - freely moving'),
    }   
    name = "NP2 w/ chronic holder"

    def __init__(self,
                 probetype,
                 chassis_type,
                 vistaplotter,
                 starting_position=(0,0,0),
                 starting_angles=(0,0,0),
                 active=True,
                 root_intersection_mesh=None,
                 **kwargs):
        self.probetype = probetype
        geometry_data = probe_geometries[probetype.replace('4a','4')]
        self.shank_offsets_um = geometry_data['shank_offsets_um'] # the offsets of the shanks in um
        self.shank_dims_um = geometry_data['shank_dims_um'] # the dimensions of one shank in um
        self.active_colors = []
        self.inactive_colors = []

        from .default_prefs import MESH_DIR

        # Retrieve the values or raise an error if not found
        try:
            mesh_file, name = self.mesh_mapping[(chassis_type, probetype)]
            self.mesh_path = MESH_DIR / mesh_file
            self.name = name
        except KeyError:
            raise ValueError(f'Invalid chassis_type "{chassis_type}" or probetype "{probetype}".')

        super().__init__(vistaplotter, starting_position, starting_angles, active, root_intersection_mesh, **kwargs)

    @property
    def shank_origins(self):
        '''Used for tracking the regions that each shank is in'''
        dims = np.stack(self.shank_dims_um) # shanks by dims
        offsets = np.stack(self.shank_offsets_um)
        offsets[:,0] = offsets[:,0] + dims[:,0] / 2
        rotated_offsets = np.dot(offsets, self.rotation_matrix.T)
        return rotated_offsets + self.origin
    
    def create_meshes(self):
        scale_factor = 1000
        if self.probetype == 'NP24':
            mesh_rotation = np.array([0,0,90])
            mesh_origin = -np.array([-32.399,-12.612, 16.973]) * 1000
        elif self.probetype == 'NP1':
            mesh_rotation = np.array([-90,0,0])
            mesh_origin = -np.array([-.081, 1.978, -9.762]) * 1000
        elif self.probetype == 'NP24a':
            mesh_rotation = np.array([0,0,90])
            mesh_origin = -np.array([-33.259, 2.768, -2.080]) * 1000
        else:
            raise ValueError(f"probetype \"{self.probetype}\" not recognized.")

        mesh = pv.read(self.mesh_path).scale(scale_factor)
        mesh = mesh.translate(mesh_origin)
        mesh = mesh.rotate_x(mesh_rotation[0])
        mesh = mesh.rotate_y(mesh_rotation[1])
        mesh = mesh.rotate_z(mesh_rotation[2])
        #rotated_translation = rotation_matrix_from_degrees(*mesh_rotation).T @ mesh_origin # the translation of the mesh must be rotated into new axes
        #mesh = mesh.translate(rotated_translation)
        self.meshes.append(mesh)
        self.active_colors.append('gray')
        self.inactive_colors.append('gray')

        for dims, offset in zip(self.shank_dims_um, self.shank_offsets_um):
            shank_vectors = np.array([[dims[0],dims[1],0], #the orthogonal set of vectors used to define a rectangle, these will be translated and rotated about the tip
                                      [dims[0],0,0],
                                      [0,0,dims[2]]])
            vecs = shank_vectors + np.array(offset).T
            self.meshes.append(pv.Rectangle(vecs.astype(np.float32)))
            self.active_colors.append(ACTIVE_COLOR)
            self.inactive_colors.append(INACTIVE_COLOR)
    
    def make_active(self):
        self.active = True
        for col,actor in zip(self.active_colors,self.actors):
            #shnk.actor.prop.opacity = 1 #FIXME: opacity not working for some reason
            actor.prop.color = col

    def make_inactive(self):
        self.active = False
        for col,actor in zip(self.inactive_colors,self.actors):
            #shnk.actor.prop.opacity = .2
            actor.prop.color = col

class CranialWindow5mm(VVASPBaseVisualizerClass):
    name = "Cranial Window - 5mm"
    def __init__(self):
        pass

class HistologyTrack(VVASPBaseVisualizerClass): # Maybe extend Probe class instead?
    # TODO: no movement, just a static mesh
    name = "Histology Track"
    def __init__(self):
        pass

class Neuron(VVASPBaseVisualizerClass):
    name = "Neuron"
    def __init__(self):
        pass



#################### GUI functionality - provide objects to the gui ####################

availible_viz_classes_for_gui = {'NP24': partial(Probe,'NP24'),
                                 'NP1': partial(Probe,'NP1'),
                                 'utah10x10': partial(Probe,'utah10x10'),
                                 'NP2 chronic holder - head fixed': partial(NeuropixelsChronicHolder,'NP24','head_fixed'),
                                 'NP2 chronic holder - freely moving': partial(NeuropixelsChronicHolder,'NP24','freely_moving'),
                                 'NP2a chronic holder - head fixed': partial(NeuropixelsChronicHolder,'NP24a','head_fixed'),
                                 'NP2a chronic holder - freely moving': partial(NeuropixelsChronicHolder,'NP24a','freely_moving'),
                                 'NP1 chronic holder - head fixed': partial(NeuropixelsChronicHolder,'NP1','head_fixed'),
                                 'NP1 chronic holder - freely moving': partial(NeuropixelsChronicHolder,'NP1','freely_moving'),
                                 'Cranial Window - 5mm [NOT IMPLEMENTED]': CranialWindow5mm,}

####### We will also expose custom mesh objects below.  #################################
# To add your own objects: 
# 1. Add your mesh to the custom_user_meshes folder
# 2. Provide the transformations in custom_user_mesh_transformations.json accordingly
# 3. They will automatically populate in the GUI
########################################################################################

custom_object_files = list((Path(preferences['user_mesh_dir'])).glob('*'))
for file in custom_object_files:
    transforms = custom_user_mesh_transformations[file.stem]
    obj = partial(CustomMeshObject, 
                  mesh_paths=file,
                  scale_factor=transforms['scale'],
                  mesh_rotation=transforms['angles'],
                  mesh_origin=transforms['origin'],)
    new_name = f'{file.stem} [CUSTOM OBJECT]'
    availible_viz_classes_for_gui[new_name] = obj