"""
Base visualization objects for VVASP
This module provides abstract base classes for visualizing probes and other objects in 3D space.
It includes functionality for:
- Basic 3D object manipulation (movement, rotation)
- Probe positioning and depth calculation
- Brain surface intersection detection
- Region boundary detection
- PyVista mesh management

The module defines two main abstract base classes:
- VVASPBaseVisualizerClass: Base class for all VVASP visualization objects
- AbstractBaseProbe: Extended base class specifically for probe visualization
"""

from .utils import *
import pyvista as pv 
from abc import ABC, abstractmethod

# Colors for active/inactive visualization states
ACTIVE_COLOR = '#FF0000'
INACTIVE_COLOR = '#000000'

# Default visualization parameters
SPHERE_RADIUS = 50
INIT_VEC = np.array([0, 10_000,0]) # Vector length chosen to ensure brain surface intersection

# Movement vectors for standard anatomical directions (in micrometers)
MOVEMENT_VECTORS = {
    'left':      np.array([-1, 0, 0]),
    'right':     np.array([1, 0, 0]),
    'dorsal':    np.array([0, 0, 1]),
    'ventral':   np.array([0, 0, -1]),
    'anterior':  np.array([0, 1, 0]),
    'posterior': np.array([0, -1, 0])
}

# Rotation vectors for standard rotational movements (in degrees)
ROTATION_VECTORS = {
    'tilt up':       np.array([1, 0, 0]),
    'tilt down':     np.array([-1, 0, 0]),
    'rotate left':   np.array([0, 0, 1]),
    'rotate right':  np.array([0, 0, -1]),
    'spin left':     np.array([0, 1, 0]),
    'spin right':    np.array([0, -1, 0])
}

class VVASPBaseVisualizerClass(ABC):
    """
    Abstract base class for VVASP visualization objects.

    This class provides core functionality for:
    - Creating and managing PyVista meshes
    - Moving and rotating objects in 3D space
    - Managing object state (active/inactive)
    - Handling PyVista actor lifecycle

    Parameters
    ----------
    vistaplotter : pyvista.Plotter, optional
        PyVista plotter instance for visualization
    starting_position : tuple, default=(0,0,0)
        Initial (x,y,z) position in micrometers
    starting_angles : tuple, default=(0,0,0)
        Initial (elevation, spin, azimuth) angles in degrees
    active : bool, default=True
        Whether the object starts in active state
    pyvista_mesh_args : dict, optional
        Keyword arguments passed to plotter.add_mesh()
    info : dict, optional
        Additional information to store with the object
    **kwargs : dict
        Additional keyword arguments
    """
    def __init__(self,
                 vistaplotter=None,
                 starting_position=(0,0,0),
                 starting_angles=(0,0,0),
                 active=True,
                 pyvista_mesh_args=None, # a list of dicts with keyword arguments for plotter.add_mesh()
                 info=None,
                 **kwargs):
        self.info = info
        if pyvista_mesh_args is None:
            pyvista_mesh_args = {}
        self.plotter = vistaplotter
        self.pyvista_mesh_args = pyvista_mesh_args
        self.active = active
        #angles[2] = -angles[2] # rotation about z is inverted for probes
        #angles[0] = -angles[0] # rotation about x is inverted for probes
        self.origin = np.array([0,0,0]) # we will move to starting_position later by calling set_location()
        self.angles = np.array([0,0,0])
        self.rotation_matrix = rotation_matrix_from_degrees(*self.angles)
        self.meshes = []
        self.actors = []
        
        if self.plotter is not None:
            self.create_meshes()
            self.spawn_actors()
        self.set_location(np.array(starting_position),np.array(starting_angles))
        
    @property
    @abstractmethod
    def name(self):
        """
        Abstract property that must be implemented by child classes.
        
        Returns
        -------
        str
            Name identifier for the visualization object
        """
        pass
    
    @abstractmethod
    def create_meshes(self) -> list[pv.PolyData]:
        """
        Abstract method to create PyVista meshes for visualization.
        
        Must be implemented by child classes to define the specific geometry
        of the visualization object. Should set self.meshes to a list of
        PyVista PolyData objects.

        Returns
        -------
        list[pv.PolyData]
            List of PyVista mesh objects
        """
        # this function must set self.meshes to a list of pyvista meshes

        # The following is just an example, replace with your mesh creation logic here
        mesh1 = pv.PolyData()  # Replace this with your actual mesh creation
        mesh2 = pv.PolyData()  # Replace this with your actual mesh creation
        self.meshes = [mesh1, mesh2]

    def spawn_actors(self):
        """
        Add mesh actors to the PyVista plotter.
        
        Creates a PyVista actor for each mesh in self.meshes and adds it
        to the plotter using the configured mesh arguments.
        """
        for mesh in self.meshes:
            self.actors.append(self.plotter.add_mesh(mesh, **self.pyvista_mesh_args))

    def set_location(self, origin, angles):
        """
        Set the absolute position and orientation of the object.

        Parameters
        ----------
        origin : array-like
            New (x,y,z) position in micrometers
        angles : array-like
            New (elevation, spin, azimuth) angles in degrees
        """
        self._rotate(angles, increment=False)
        self._move(origin, increment=False)
                        
    def move(self, direction, multiplier):
        """
        Move or rotate the object in a specified direction.

        Parameters
        ----------
        direction : str
            One of:
            - 'left', 'right', 'dorsal', 'ventral', 'anterior', 'posterior' for translation
            - 'tilt up', 'tilt down', 'rotate left', 'rotate right', 'spin left', 'spin right' for rotation
            - 'retract', 'advance' for probe-specific movement
            - 'home' to reset position
        multiplier : float
            Distance in micrometers for translation, or angle in degrees for rotation
        """
        if direction in MOVEMENT_VECTORS:
            self._move(MOVEMENT_VECTORS[direction] * multiplier)
        elif direction in ROTATION_VECTORS:
            self._rotate(ROTATION_VECTORS[direction] * multiplier)
        elif direction in {'retract', 'advance'}:
            sign = 1 if direction == 'retract' else -1
            position_shift = sign * move3D(multiplier, *self.angles[[0, 2]])
            self._move(position_shift.astype(int))
        elif direction == 'home':
            self._move(np.array([0, 0, 0]), increment=False)
            self._rotate(np.array([90, 0, 0]), increment=False)

    def _move(self, position_shift, increment=True, **kwargs):
        """
        Internal method to handle object translation.

        Parameters
        ----------
        position_shift : array-like
            Vector to translate by in micrometers
        increment : bool, default=True
            If True, add to current position; if False, set absolute position
        **kwargs : dict
            Additional keyword arguments

        Raises
        ------
        ValueError
            If position_shift does not have exactly 3 components
        """
        if increment:
            self.origin += position_shift
        else:
            assert len(position_shift) == 3, ValueError('Position has to be 3 values') 
            old_position = np.array(self.origin)
            self.origin[:] = position_shift 
            position_shift = position_shift - old_position
        # move the meshes
        if self.plotter is not None:
            for i,mesh in enumerate(self.meshes):
                mesh.shallow_copy(mesh.translate(position_shift))
    
    def _rotate(self, angle_shift, increment=True, **kwargs):
        """
        Internal method to handle object rotation.

        Parameters
        ----------
        angle_shift : array-like
            Vector of rotation angles in degrees (elevation, spin, azimuth)
        increment : bool, default=True
            If True, add to current angles; if False, set absolute angles
        **kwargs : dict
            Additional keyword arguments

        Raises
        ------
        ValueError
            If angle_shift does not have exactly 3 components
        """
        if increment:
            self.angles[:] += angle_shift
        else:
            assert len(angle_shift) == 3, ValueError('Angle has to be 3 values') 
            self.angles[:] = angle_shift 
        # rotate the meshes
        old_rotation_matrix = self.rotation_matrix
        self.rotation_matrix = rotation_matrix_from_degrees(*self.angles)
        if self.plotter is not None:
            for i,mesh in enumerate(self.meshes):
                # rotations are performed relative to the objects origin, not the origin of the pyvista scene
                # So we need to translate the mesh to the pyvista origin, rotate it, and then translate it back to its original spot
                points = old_rotation_matrix.T @ (mesh.points - self.origin).T
                mesh.points = (self.rotation_matrix @ points).T + self.origin
                mesh.shallow_copy(mesh)
            
    def make_active(self):
        """
        Set the object to active state and update its visual appearance.
        """
        self.active = True
        for actor in self.actors:
            actor.prop.color = ACTIVE_COLOR

    def make_inactive(self):
        """
        Set the object to inactive state and update its visual appearance.
        """
        self.active = False
        for actor in self.actors:
            actor.prop.color = INACTIVE_COLOR
    
    def __del__(self):
        """
        Clean up PyVista actors when the object is deleted.
        """
        if self.plotter is None:
            return
        for actor in self.actors:
            self.plotter.remove_actor(actor)
    
class AbstractBaseProbe(VVASPBaseVisualizerClass):
    """
    Abstract base class for probe visualization objects.

    Extends VVASPBaseVisualizerClass with probe-specific functionality:
    - Brain surface entry point calculation
    - Probe depth computation
    - Region intersection detection
    - Multi-shank support

    This class can be used with CustomMeshObject or other PyVista mesh definitions
    to visualize arbitrary probe geometries in the VVASP scene.

    Parameters
    ----------
    vistaplotter : pyvista.Plotter
        PyVista plotter instance for visualization
    starting_position : tuple, default=(0,0,0)
        Initial (x,y,z) position in micrometers
    starting_angles : tuple, default=(0,0,0)
        Initial (elevation, spin, azimuth) angles in degrees
    active : bool, default=True
        Whether the probe starts in active state
    root_intersection_mesh : pyvista.PolyData, optional
        Mesh representing the brain surface for intersection calculations
    **kwargs : dict
        Additional keyword arguments passed to VVASPBaseVisualizerClass
    """
    def __init__(self,
                 vistaplotter,
                 starting_position=(0,0,0),
                 starting_angles=(0,0,0),
                 active=True,
                 root_intersection_mesh=None,
                 **kwargs):
        self.entry_point = None
        self.intersection_vector = None # an imaginary line from shank origin, used for calculating the intersection with regions and the brain surface

        #the following mesh and actor are used to visualize the brain surface entry point
        #they are the result of a ray trace from the probe origin to the brain surface and obey unique logic
        #thus we will handle them separately from the other meshes
        if root_intersection_mesh is not None:
            self.root_intersection_mesh = root_intersection_mesh
        if vistaplotter is not None:
            self.ball_mesh = pv.Sphere(center=np.array(starting_position).astype(np.float32), radius=SPHERE_RADIUS)
            self.ball_actor = vistaplotter.add_mesh(self.ball_mesh, color='blue')

        super().__init__(vistaplotter, starting_position, starting_angles, active, **kwargs)

        if self.plotter is not None:
            if active:
                self.make_active()
            else:
                self.make_inactive()

    @property
    @abstractmethod
    def shank_origins(self):
        """
        Abstract property defining probe shank origins.

        Must be implemented by child classes to specify the origin points
        of each shank for region intersection calculations.

        Returns
        -------
        ndarray
            Array of shape (n_shanks, 3) specifying the origin of each shank
        """
        pass

    def drive_probe_from_entry(self, ml_ap_entry, angles, depth, root_mesh=None):
        """
        Position probe at a specific entry point and drive to target depth.

        Parameters
        ----------
        ml_ap_entry : array-like
            (ML, AP) coordinates of desired entry point in micrometers
        angles : array-like
            (elevation, spin, azimuth) angles in degrees
        depth : float
            Target depth along probe axis in micrometers
        root_mesh : pyvista.PolyData, optional
            Brain surface mesh for intersection calculations
        """
        if root_mesh is not None:
            self.root_intersection_mesh = root_mesh

        # 1) place the probe 1000um above the entry point
        above_entrypoint = np.concatenate([np.array(ml_ap_entry), np.array([1000])])
        self.set_location(above_entrypoint, np.array(angles))

        # 2) lower the probe to the entry point
        # since we need to find the entry point and are above the target, ray trace straight down to find mesh surface
        STRAIGHT_DOWN_VECTOR = np.array([0, 0, -10_000])
        end = STRAIGHT_DOWN_VECTOR + self.origin
        start = self.origin.astype(np.float32)
        intersection_points = self.root_intersection_mesh.ray_trace(start, end)[0]
        entry_point = intersection_points[np.argmax(intersection_points[:,2]),:].flatten()
        self.set_location(entry_point, angles)

        # 3) advance the probe to the desired depth
        self.move('advance', depth)
    
    def ray_trace_intersection(self, mesh):
        """
        Calculate intersection points between probe trajectory and a mesh.

        Parameters
        ----------
        mesh : pyvista.PolyData
            Mesh to calculate intersections with

        Returns
        -------
        ndarray
            Array of intersection points
        """
        # 1. Compute the intersection point with the brain surface and update the plotter
        init_vector = (self.rotation_matrix @ INIT_VEC)
        self.intersection_vector = init_vector + self.origin
        start = self.origin.astype(np.float32)
        end = self.intersection_vector.astype(np.float32)
        points = mesh.ray_trace(start, end)[0]
        return points
    
    def compute_region_intersections(self, vvasp_atlas):
        """
        Calculate brain regions intersected by each probe shank.

        Parameters
        ----------
        vvasp_atlas : VVASPAtlas
            Atlas object for region lookup

        Returns
        -------
        tuple
            (region_boundary_distances, region_acronyms)
            - region_boundary_distances: list of arrays with distances to region boundaries for each shank
            - region_acronyms: list of lists with region acronyms for each shank
        """
        # TODO: optionally take a channelmap
        region_boundary_distances = [None] * len(self.shank_origins)
        region_acronyms = [None] * len(self.shank_origins)

        init_vector = (self.rotation_matrix @ INIT_VEC)
        for i,shnk_origin in enumerate(self.shank_origins):
            shnk_ending = init_vector + shnk_origin
            atlas_vector = vvasp_atlas.bregma_positions_to_atlas_voxels([shnk_origin, shnk_ending])
            atlas_bresenham_line = bresenham3D(atlas_vector[0], atlas_vector[1]) # get the voxels that the probe passes thru 
            region_boundary_voxels, midpoint_voxels = vvasp_atlas.atlas_voxels_to_annotation_boundaries(atlas_bresenham_line, return_midpoints=True)
            region_acronyms[i] = [vvasp_atlas.structure_from_coords(a, as_acronym=True) for a in midpoint_voxels]
            # Convert midpoints and boundaries to single distance values
            region_boundary_voxels = region_boundary_voxels * vvasp_atlas.resolution # convert to um
            zero_point = region_boundary_voxels[0]
            region_boundary_distances[i] = np.linalg.norm(region_boundary_voxels - zero_point, axis=1)
        return region_boundary_distances, region_acronyms

    def set_location(self, origin, angles):
        """
        Set probe position and update entry point visualization.

        Parameters
        ----------
        origin : array-like
            New (x,y,z) position in micrometers
        angles : array-like
            New (elevation, spin, azimuth) angles in degrees
        """
        super().set_location(origin, angles)
        if hasattr(self, 'root_intersection_mesh') and self.plotter is not None:
            self._update_entry_point_mesh()
            
    def move(self, direction, multiplier):
        """
        Move probe and update entry point visualization.

        Parameters
        ----------
        direction : str
            Movement direction
        multiplier : float
            Movement magnitude
        """
        super().move(direction, multiplier)
        if hasattr(self, 'root_intersection_mesh') and self.plotter is not None:
            self._update_entry_point_mesh()
    
    def _update_entry_point_mesh(self):
        """
        Update the visualization of the brain surface entry point.
        
        Calculates new intersection point with brain surface and updates
        the position of the entry point marker sphere.
        """
        if self.root_intersection_mesh is not None: 
            points = self.ray_trace_intersection(self.root_intersection_mesh)
            if points.shape[0] == 1:
                self.entry_point = points[0,:].flatten()
                self.ball_mesh.shallow_copy(pv.Sphere(center=points, radius=SPHERE_RADIUS))
            elif points.shape[0] > 1: #pick the point with the highest z value if there are multiple
                self.entry_point = points[np.argmax(points[:,2]),:].flatten()
                self.ball_mesh.shallow_copy(pv.Sphere(center=self.entry_point, radius=SPHERE_RADIUS))
            else:
                self.entry_point = None
                self.ball_mesh.shallow_copy(pv.Sphere(center=self.origin, radius=SPHERE_RADIUS))
        else:
            self.ball_mesh.shallow_copy(pv.Sphere(center=self.origin, radius=SPHERE_RADIUS))
    
    @property
    def depth(self):
        """
        Calculate current probe depth.

        Returns
        -------
        float
            Distance from entry point to probe tip in micrometers.
            Returns 0 if no entry point is defined.
        """
        if self.entry_point is None:
            return 0
        else:
            return np.linalg.norm(self.origin-self.entry_point)
            
    @property
    def probe_properties(self):
        origin = self.origin.tolist()
        angles = self.angles.tolist()
        entry_point = self.entry_point.tolist() if self.entry_point is not None else [None,None,None]
        return dict(probetype=self.name,
                    info=self.info,
                    active=self.active,
                    tip=dict(AP=origin[1],
                             ML=origin[0],
                             DV=origin[2]),
                    angles=dict(elevation=angles[0],
                                azimuth=angles[2],
                                spin=angles[1]),
                    entrypoint=dict(AP=entry_point[1],
                                    ML=entry_point[0],
                                    DV=entry_point[2]),
                    depth_along_probe_axis=self.depth)
    def __del__(self):
        self.plotter.remove_actor(self.ball_actor)
        super().__del__()