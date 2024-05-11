from .utils import *
from .io import probe_geometries
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
                 active=True,):
        self.mesh_paths = mesh_paths
        self.scale_factor = scale_factor
        self.mesh_origin = mesh_origin
        self.mesh_rotation = mesh_rotation
        super().__init__(vistaplotter, starting_position, starting_angles, active, pyvista_mesh_args)


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
                 ray_trace_intersection=True,
                 root_intersection_mesh=None):
        geometry_data = probe_geometries[probetype]
        self.probetype = probetype
        self.shank_offsets_um = geometry_data['shank_offsets_um'] # the offsets of the shanks in um
        self.shank_dims_um = geometry_data['shank_dims_um'] # the dimensions of one shank in um
        super().__init__(vistaplotter, starting_position, starting_angles, active, ray_trace_intersection, root_intersection_mesh)
    
    def create_meshes(self):
        for dims, offset in zip(self.shank_dims_um, self.shank_offsets_um):
            shank_vectors = np.array([[dims[0],dims[1],0], #the orthogonal set of vectors used to define a rectangle, these will be translated and rotated about the tip
                                      [dims[0],0,0],
                                      [0,0,dims[2]]])
            vecs = shank_vectors + np.array(offset).T
            self.meshes.append(pv.Rectangle(vecs.astype(np.float32)))

class Neuropixels2Chronic(AbstractBaseProbe):
    name = "NP2 w/ chronic holder"
    def __init__(self,
                 chassis_type,
                 vistaplotter,
                 starting_position=(0,0,0),
                 starting_angles=(0,0,0),
                 active=True,
                 ray_trace_intersection=True,
                 root_intersection_mesh=None):
        probetype = 'NP24'
        geometry_data = probe_geometries[probetype]
        self.probetype = probetype
        self.shank_offsets_um = geometry_data['shank_offsets_um'] # the offsets of the shanks in um
        self.shank_dims_um = geometry_data['shank_dims_um'] # the dimensions of one shank in um
        self.active_colors = []
        self.inactive_colors = []

        from .default_prefs import MESH_DIR
        if chassis_type == 'head_fixed':
            self.mesh_path = MESH_DIR / 'np2_head_fixed.stl'
        elif chassis_type == 'freely_moving':
            self.mesh_path = MESH_DIR / 'np2_freely_moving.stl'
        else:
            raise ValueError(f"chassis_type \"{chassis_type}\" not recognized.") 
        super().__init__(vistaplotter, starting_position, starting_angles, active, ray_trace_intersection, root_intersection_mesh)
    
    def create_meshes(self):
        scale_factor = 1000
        mesh_rotation = np.array([180,0,90])
        mesh_origin = -np.array([-30.399,-12.612, 16.973]) * 1000

        mesh = pv.read(self.mesh_path).scale(scale_factor)
        mesh = mesh.translate(mesh_origin)
        mesh = mesh.rotate_x(mesh_rotation[0])
        mesh = mesh.rotate_y(mesh_rotation[1])
        mesh = mesh.rotate_z(mesh_rotation[2])
        #rotated_translation = rotation_matrix_from_degrees(*self.mesh_rotation).T @ self.mesh_origin # the translation of the mesh must be rotated into new axes
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
        self.plotter.update()

    def make_inactive(self):
        self.active = False
        for col,actor in zip(self.inactive_colors,self.actors):
            #shnk.actor.prop.opacity = .2
            actor.prop.color = col
        self.plotter.update()

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


#def get_classes():
#    import inspect
#    current_module = sys.modules[__name__]
#    classes = {}
#    for name, obj in inspect.getmembers(current_module):
#        if inspect.isclass(obj) and inspect.getmodule(obj) == current_module:
#            classes.update({obj.name: obj})
#    classes.pop('Probe')
#    for prbname in probe_geometries.keys():
#        classes.update({prbname: Probe})
#    return classes

availible_viz_classes_for_gui = {'CustomMeshObject': CustomMeshObject, #objects availible to the PyQt GUI
                                 'NP24': Probe,
                                 'NP1': Probe,
                                 'utah10x10': Probe,
                                 'NP2 w/ chronic holder': Neuropixels2Chronic,
                                 'Cranial Window - 5mm': CranialWindow5mm,}