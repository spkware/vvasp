from .utils import *
from .io import probe_geometries
from .BaseVizClasses import VVASPBaseVisualizerClass, AbstractBaseProbe

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
                 starting_position=(0,0,0),
                 starting_angles=(0,0,0),
                 active=True,):
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
        meshes = []
        for dims, offset in zip(self.shank_dims_um, self.shank_offsets_um):
            shank_vectors = np.array([[dims[0],dims[1],0], #the orthogonal set of vectors used to define a rectangle, these will be translated and rotated about the tip
                                      [dims[0],0,0],
                                      [0,0,dims[2]]])
            vecs = shank_vectors + np.array(offset).T
            meshes.append(pv.Rectangle(vecs.astype(np.float32)))
        self.meshes = meshes
class Neuropixels2Chronic(CustomMeshObject, AbstractBaseProbe):
    name = "NP2 w/ chronic holder"
    def __init__(self):
        pass
    #raise NotImplementedError("This class is not yet implemented")
    # This class will implement the chronic holder as an example of how we can use the CustomMeshObject class
    # to handle moving meshes around and how to implement new funcitonality if desired.

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


def get_classes():
    import inspect
    current_module = sys.modules[__name__]
    classes = {}
    for name, obj in inspect.getmembers(current_module):
        if inspect.isclass(obj) and inspect.getmodule(obj) == current_module:
            classes.update({obj.name: obj})
    classes.pop('Probe')
    for prbname in probe_geometries.keys():
        classes.update({prbname: Probe})
    return classes

availible_viz_classes_for_gui = {'CustomMeshObject': CustomMeshObject, #objects availible to the PyQt GUI
                                 'NP24': Probe,
                                 'NP1': Probe,
                                 'utah10x10': Probe,
                                 'NP2 w/ chronic holder': Neuropixels2Chronic,
                                 'Cranial Window - 5mm': CranialWindow5mm,}