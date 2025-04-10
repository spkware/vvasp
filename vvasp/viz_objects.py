"""
Visualization objects for VVASP 

This module provides concrete implementations of visualization objects including:
- Custom mesh objects for user-defined geometries
- Probe visualizations for various probe types (Neuropixels, Utah array)
- Chronic holder visualizations (Neuropixels chronic holders)
- Additional experimental equipment (cranial windows, etc.)

The module also provides a registry of available visualization classes for the GUI.
"""

from .utils import *
from .io import probe_geometries, preferences, custom_user_mesh_transformations
from .base_viz_objects import VVASPBaseVisualizerClass, AbstractBaseProbe, ACTIVE_COLOR, INACTIVE_COLOR

class CustomMeshObject(VVASPBaseVisualizerClass):
    """
    Custom mesh visualization object that loads user-provided mesh files.

    This class allows users to load and visualize their own mesh files in the VVASP scene.
    Handles mesh transformations, scaling, and positioning.

    Parameters
    ----------
    mesh_paths : str or Path or list
        Path(s) to mesh file(s) to load
    vistaplotter : pyvista.Plotter
        PyVista plotter instance for visualization
    scale_factor : float, default=1000.0
        Scaling factor to convert mesh units (typically mm) to scene units (μm)
    pyvista_mesh_args : dict, optional
        Keyword arguments passed to pv.read()
    mesh_origin : tuple, default=(0,0,0)
        Origin point for mesh rotations
    mesh_rotation : tuple, default=(0,0,0)
        Initial rotation angles (degrees) to apply to mesh
    starting_position : tuple, default=(0,0,0)
        Initial position in scene
    starting_angles : tuple, default=(0,0,0)
        Initial rotation angles in scene
    active : bool, default=True
        Whether object starts in active state
    **kwargs : dict
        Additional keyword arguments passed to VVASPBaseVisualizerClass
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
        """
        Create PyVista meshes from provided mesh files.
        
        Applies scaling, translation, and rotation according to initialization parameters.
        """
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
    """
    Base probe visualization object for various probe types.

    Visualizes probes based on geometry specifications from probe_geometries.
    Supports multi-shank probes with customizable dimensions and offsets.

    Parameters
    ----------
    probetype : str
        Type of probe to visualize (e.g., 'NP24', 'NP1', 'utah10x10')
    vistaplotter : pyvista.Plotter, optional
        PyVista plotter instance for visualization
    starting_position : tuple, default=(0,0,0)
        Initial probe tip position
    starting_angles : tuple, default=(0,0,0)
        Initial probe rotation angles
    active : bool, default=True
        Whether probe starts in active state
    root_intersection_mesh : pyvista.PolyData, optional
        Brain surface mesh for intersection calculations
    **kwargs : dict
        Additional keyword arguments passed to AbstractBaseProbe
    """
    def __init__(self,
                 probetype,
                 vistaplotter=None,
                 starting_position=(0,0,0),
                 starting_angles=(0,0,0),
                 active=True,
                 root_intersection_mesh=None,
                 **kwargs):
        # Replace NP24a with NP24 for geometry lookup
        geometry_lookup_type = probetype.replace('4a', '4')
        geometry_data = probe_geometries[geometry_lookup_type]
        self.probetype = probetype
        self.shank_offsets_um = geometry_data['shank_offsets_um'] # the offsets of the shanks in um
        self.shank_dims_um = geometry_data['shank_dims_um'] # the dimensions of one shank in um
        super().__init__(vistaplotter, starting_position, starting_angles, active, root_intersection_mesh, **kwargs)
        self._name = probetype  # Set name after parent initialization
    
    @property
    def name(self):
        """Return the name of the probe type."""
        return self._name

    def create_meshes(self):
        """
        Create rectangular meshes for each probe shank.
        
        Uses shank dimensions and offsets from probe geometry specification.
        """
        for dims, offset in zip(self.shank_dims_um, self.shank_offsets_um):
            shank_vectors = np.array([[dims[0],dims[1],0], #the orthogonal set of vectors used to define a rectangle, these will be translated and rotated about the tip
                                      [dims[0],0,0],
                                      [0,0,dims[2]]])
            vecs = shank_vectors + np.array(offset).T
            self.meshes.append(pv.Rectangle(vecs.astype(np.float32)))

    @property
    def shank_origins(self):
        """
        Calculate current positions of probe shank origins.

        Returns
        -------
        ndarray
            Array of shape (n_shanks, 3) with current shank origin coordinates
        """
        dims = np.stack(self.shank_dims_um) # shanks by dims
        offsets = np.stack(self.shank_offsets_um)
        offsets[:,0] = offsets[:,0] + dims[:,0] / 2 
        offsets[:,2] = offsets[:,2] + dims[:,2] / 2 
        rotated_offsets = np.dot(offsets, self.rotation_matrix.T)
        return rotated_offsets + self.origin

class NeuropixelsChronicHolder(Probe):
    """
    Visualization object for Neuropixels chronic holder assemblies.

    Combines probe visualization with appropriate chronic holder mesh.
    Supports different configurations (head-fixed/freely-moving) for various
    Neuropixels probe types.

    Parameters
    ----------
    probetype : str
        Type of Neuropixels probe ('NP24', 'NP24a', 'NP1')
    chassis_type : str
        Type of holder chassis ('head_fixed' or 'freely_moving')
    vistaplotter : pyvista.Plotter, optional
        PyVista plotter instance for visualization
    starting_position : tuple, default=(0,0,0)
        Initial holder position
    starting_angles : tuple, default=(0,0,0)
        Initial holder rotation angles
    active : bool, default=True
        Whether holder starts in active state
    root_intersection_mesh : pyvista.PolyData, optional
        Brain surface mesh for intersection calculations
    **kwargs : dict
        Additional keyword arguments passed to Probe

    Raises
    ------
    ValueError
        If invalid probetype or chassis_type is provided
    """
    # Define mapping of (chassis_type, probetype) to the mesh file and name that gets logged to the experiment file
    MESH_MAPPING = {
        ('head_fixed', 'NP24'): ('np2_head_fixed.stl', 'NP2 chronic holder - head fixed'),
        ('freely_moving', 'NP24'): ('np2_freely_moving.stl', 'NP2 chronic holder - freely moving'),
        ('head_fixed', 'NP24a'): ('np2a_head_fixed.stl', 'NP2a chronic holder - head fixed'),
        ('freely_moving', 'NP24a'): ('np2a_freely_moving.stl', 'NP2a chronic holder - freely moving'),
        ('head_fixed', 'NP1'): ('np1_head_fixed.stl', 'NP1 chronic holder - head fixed'),
        ('freely_moving', 'NP1'): ('np1_freely_moving.stl', 'NP1 chronic holder - freely moving'),
    }   
    name = "NP2 w/ chronic holder"

    # Constants for mesh transformations
    SCALE_FACTOR = 1000
    MESH_TRANSFORMATIONS = {
        'NP24': {
            'rotation': np.array([0,0,90]),
            'origin': -np.array([-32.399,-12.612, 16.973]) * 1000
        },
        'NP1': {
            'rotation': np.array([-90,0,0]),
            'origin': -np.array([-.081, 1.978, -9.762]) * 1000
        },
        'NP24a': {
            'rotation': np.array([0,0,90]),
            'origin': -np.array([-33.259, 2.768, -2.080]) * 1000
        }
    }

    def __init__(self,
                 probetype,
                 chassis_type,
                 vistaplotter=None,
                 starting_position=(0,0,0),
                 starting_angles=(0,0,0),
                 active=True,
                 root_intersection_mesh=None,
                 **kwargs):
        # First set up the mesh path and name
        from .default_prefs import MESH_DIR
        try:
            mesh_file, name = self.MESH_MAPPING[(chassis_type, probetype)]
            self.mesh_path = MESH_DIR / mesh_file
            self.name = name
        except KeyError:
            raise ValueError(f'Invalid chassis_type "{chassis_type}" or probetype "{probetype}".')

        # Initialize color lists before parent initialization
        self.active_colors = []
        self.inactive_colors = []

        # Initialize the base Probe class
        super().__init__(probetype, vistaplotter, starting_position, starting_angles, active, root_intersection_mesh, **kwargs)
        
    def create_meshes(self):
        if self.probetype not in self.MESH_TRANSFORMATIONS:
            raise ValueError(f"probetype \"{self.probetype}\" not recognized.")

        transforms = self.MESH_TRANSFORMATIONS[self.probetype]
        mesh = pv.read(self.mesh_path).scale(self.SCALE_FACTOR)
        mesh = mesh.translate(transforms['origin'])
        mesh.points = np.dot(mesh.points, rotation_matrix_from_degrees(*transforms['rotation'],order='xyz').T)
        self.meshes.append(mesh)
        self.active_colors.append('gray')
        self.inactive_colors.append('gray')

        # Call the parent class's create_meshes to handle the probe shanks
        super().create_meshes()
        # Add colors for the shanks
        for _ in self.shank_dims_um:
            self.active_colors.append(ACTIVE_COLOR)
            self.inactive_colors.append(INACTIVE_COLOR)
    
class CranialWindow5mm(VVASPBaseVisualizerClass):
    """Placeholder for 5mm cranial window visualization."""
    name = "Cranial Window - 5mm"
    def __init__(self):
        pass

class HistologyTrack(VVASPBaseVisualizerClass):
    """Placeholder for histology track visualization."""
    name = "Histology Track"
    def __init__(self):
        pass

class Neuron(VVASPBaseVisualizerClass):
    """Placeholder for neuron visualization."""
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