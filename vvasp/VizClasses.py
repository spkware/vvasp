from .utils import *
from .BaseVizClasses import VVASPBaseVisualizerClass, Probe
from pyvista import read as pvread

class CustomMeshObject(VVASPBaseVisualizerClass):
    """
    This class extends the VVASPBaseVisualizerClass and allows the user to load their own mesh files
    into the pyvista scene. The base class handles the logic for moving the mesh, making it active, etc.

    """
    def __init__(self,
                 mesh_paths,
                 vistaplotter,
                 pyvista_mesh_args=None, # a list of dicts with keyword arguments for pv.read()
                 starting_position=(0,0,0),
                 starting_angles=(0,0,0),
                 active=True,):
        self.name = "CustomMeshObject"
        self.mesh_paths = mesh_paths
        super().__init__(vistaplotter, starting_position, starting_angles, active,)

    def create_meshes(self):
        # Your mesh creation logic here
        # TODO: add a way to define transformations
        # TODO: define a new origin for the mesh 
        meshes = []
        for p in self.mesh_paths:
            meshes.append(pvread(p))
        self.meshes = meshes

class Neuropixels2_4Shank(Probe):
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
        super().__init__(vistaplotter, starting_position, starting_angles, active)
    
    def create_meshes(self):
        shank_vectors = np.array([[self.SHANK_DIMS_UM[0],self.SHANK_DIMS_UM[1],0], #the orthogonal set of vectors used to define a rectangle, these will be translated and rotated about the tip
                                  [self.SHANK_DIMS_UM[0],0,0],
                                  [0,0,self.SHANK_DIMS_UM[2]]])
        meshes = []
        for offset in self.PROBE_OFFSETS_UM:
            vecs = shank_vectors + np.array([offset,0,0]).T
            #vecs = shank_vectors
            meshes.append(pv.Rectangle(vecs))
        self.meshes = meshes

#class Neuropixels1(Probe):
#    def __init__(self):
#        raise NotImplementedError("This class is not yet implemented")
#    def create_meshes(self):
#        raise NotImplementedError("This class is not yet implemented")

class Neuropixels2Chronic(CustomMeshObject, Probe):
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

     