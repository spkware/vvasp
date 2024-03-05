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
                 active=True,
                 ray_trace_intersection=True,
                 intersection_meshes=None):
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
    def __init__(self,
                 mesh_paths,
                 vistaplotter,
                 starting_position=(0,0,0),
                 starting_angles=(0,0,0),
                 active=True,
                 ray_trace_intersection=True,
                 intersection_meshes=None):
        self.name = "Neuropixels2.0 - 4Shank"
        self.mesh_paths = mesh_paths
        super().__init__(vistaplotter, starting_position, starting_angles, active, ray_trace_intersection, intersection_meshes)
    
    def create_meshes(self):
        raise NotImplementedError("This class is not yet implemented")

class Neuropixels1(Probe):
    def __init__(self,
                 mesh_paths,
                 vistaplotter,
                 starting_position=(0,0,0),
                 starting_angles=(0,0,0),
                 active=True,
                 ray_trace_intersection=True,
                 intersection_meshes=None):
        self.name = "Neuropixels1.0"
        self.mesh_paths = mesh_paths
        super().__init__(vistaplotter, starting_position, starting_angles, active, ray_trace_intersection, intersection_meshes)
    
    def create_meshes(self):
        raise NotImplementedError("This class is not yet implemented")

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

     