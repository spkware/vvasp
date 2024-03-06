from .utils import *
from .io import probe_geometries
from .BaseVizClasses import VVASPBaseVisualizerClass, AbstractBaseProbe

class CustomMeshObject(VVASPBaseVisualizerClass):
    """
    This class extends the VVASPBaseVisualizerClass and allows the user to load their own mesh files
    into the pyvista scene. The base class handles the logic for moving the mesh, making it active, etc.

    """
    def __init__(self,
                 mesh_paths,
                 vistaplotter,
                 scale_factor=1.0,
                 pyvista_mesh_args=None, # a list of dicts with keyword arguments for pv.read()
                 starting_position=(0,0,0),
                 starting_angles=(0,0,0),
                 active=True,):
        self.name = "CustomMeshObject"
        self.mesh_paths = mesh_paths
        self.scale_factor = scale_factor
        super().__init__(vistaplotter, starting_position, starting_angles, active,)

    def create_meshes(self):
        # Your mesh creation logic here
        # TODO: add a way to define transformations
        # TODO: define a new origin for the mesh 
        meshes = []
        for p in self.mesh_paths:
            meshes.append(pv.read(p).scale(self.scale_factor))
        self.meshes = meshes

class Probe(AbstractBaseProbe):
    def __init__(self,
                 probetype,
                 vistaplotter,
                 starting_position=(0,0,0),
                 starting_angles=(0,0,0),
                 active=True,
                 ray_trace_intersection=True,
                 intersection_meshes=None):
        geometry_data = probe_geometries[probetype]
        self.name = geometry_data['full_name']
        self.shank_offsets_um = geometry_data['shank_offsets_um'] # the offsets of the shanks in um
        self.shank_dims_um = geometry_data['shank_dims_um'] # the dimensions of one shank in um
        super().__init__(vistaplotter, starting_position, starting_angles, active, ray_trace_intersection, intersection_meshes)
    
    def create_meshes(self):
        meshes = []
        for dims, offset in zip(self.shank_dims_um, self.shank_offsets_um):
            shank_vectors = np.array([[dims[0],dims[1],0], #the orthogonal set of vectors used to define a rectangle, these will be translated and rotated about the tip
                                      [dims[0],0,0],
                                      [0,0,dims[2]]])
            vecs = shank_vectors + np.array(offset).T
            meshes.append(pv.Rectangle(vecs))
        self.meshes = meshes

class Neuropixels2_4Shank(AbstractBaseProbe):
    PROBE_OFFSETS_UM = (-410,-160,90,340) # the offsets of the shanks in um
    SHANK_DIMS_UM = np.array([70,-10_000,0]) # the dimensions of one shank in um
    def __init__(self,
                 vistaplotter,
                 starting_position=(0,0,0),
                 starting_angles=(0,0,0),
                 active=True,
                 ray_trace_intersection=True,
                 intersection_meshes=None):
        self.name = "Neuropixels2.0 - 4Shank"
        super().__init__(vistaplotter, starting_position, starting_angles, active, ray_trace_intersection, intersection_meshes)
    
    def create_meshes(self):
        shank_vectors = np.array([[self.SHANK_DIMS_UM[0],self.SHANK_DIMS_UM[1],0], #the orthogonal set of vectors used to define a rectangle, these will be translated and rotated about the tip
                                  [self.SHANK_DIMS_UM[0],0,0],
                                  [0,0,self.SHANK_DIMS_UM[2]]])
        meshes = []
        for offset in self.PROBE_OFFSETS_UM:
            vecs = shank_vectors + np.array([offset,0,0]).T
            meshes.append(pv.Rectangle(vecs))
        self.meshes = meshes

class Neuropixels1(AbstractBaseProbe):
    PROBE_OFFSET_UM = -35 # the offsets of the shanks in um
    SHANK_DIMS_UM = np.array([70,-10_000,0]) # the dimensions of one shank in um
    def __init__(self,
                 vistaplotter,
                 starting_position=(0,0,0),
                 starting_angles=(0,0,0),
                 active=True,
                 ray_trace_intersection=True,
                 intersection_meshes=None):
        self.name = "Neuropixels1.0"
        super().__init__(vistaplotter, starting_position, starting_angles, active, ray_trace_intersection, intersection_meshes)
    
    def create_meshes(self):
        shank_vectors = np.array([[self.SHANK_DIMS_UM[0],self.SHANK_DIMS_UM[1],0], #the orthogonal set of vectors used to define a rectangle, these will be translated and rotated about the tip
                                  [self.SHANK_DIMS_UM[0],0,0],
                                  [0,0,self.SHANK_DIMS_UM[2]]])
        vecs = shank_vectors + np.array([self.PROBE_OFFSET_UM,0,0]).T
        self.meshes = [pv.Rectangle(vecs)]

class Neuropixels2Chronic(CustomMeshObject, AbstractBaseProbe):
    pass
    #raise NotImplementedError("This class is not yet implemented")
    # This class will implement the chronic holder as an example of how we can use the CustomMeshObject class
    # to handle moving meshes around and how to implement new funcitonality if desired.

class CranialWindow5mm(VVASPBaseVisualizerClass):
    pass
    #raise NotImplementedError("This class is not yet implemented")

class HistologyTrack(VVASPBaseVisualizerClass): # Maybe extend Probe class instead?
    # TODO: no movement, just a static mesh
    pass
    #raise NotImplementedError("This class is not yet implemented")

class Neuron(VVASPBaseVisualizerClass):
    pass
    #raise NotImplementedError("This class is not yet implemented")

     