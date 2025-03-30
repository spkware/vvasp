from .utils import *
import pyvista as pv 
from abc import ABC, abstractmethod

ACTIVE_COLOR = '#FF0000'
INACTIVE_COLOR = '#000000'
SPHERE_RADIUS = 50
INIT_VEC = np.array([0, 10_000,0]) # just has to be long enough to intersect the brain surface


MOVEMENT_VECTORS = {
    'left':      np.array([-1, 0, 0]),
    'right':     np.array([1, 0, 0]),
    'dorsal':    np.array([0, 0, 1]),
    'ventral':   np.array([0, 0, -1]),
    'anterior':  np.array([0, 1, 0]),
    'posterior': np.array([0, -1, 0])
}

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
    An absttract base class (can not be instantiated) that will be inherited
    by child classes for visualization in vvasp. This handles the drawing and movement of meshes

    Max Melin, 2024
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
    def name():
        pass
    
    @abstractmethod
    def create_meshes(self) -> list[pv.PolyData]:
        # defined in child classes
        # this function must set self.meshes to a list of pyvista meshes

        # The following is just an example, replace with your mesh creation logic here
        mesh1 = pv.PolyData()  # Replace this with your actual mesh creation
        mesh2 = pv.PolyData()  # Replace this with your actual mesh creation
        self.meshes = [mesh1, mesh2]

    def spawn_actors(self):
        #add the actors to the plotter
        for mesh in self.meshes:
            self.actors.append(self.plotter.add_mesh(mesh, **self.pyvista_mesh_args))

    def set_location(self,origin,angles):
        self._rotate(angles,increment = False)
        self._move(origin,increment = False)
                        
    def move(self, direction, multiplier):
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
        if increment:
            self.origin += position_shift
        else:
            assert len(position_shift) == 3,ValueError('Position has to be 3 values') 
            old_position = np.array(self.origin)
            self.origin[:] = position_shift 
            position_shift = position_shift - old_position
        # move the meshes
        if self.plotter is not None:
            for i,mesh in enumerate(self.meshes):
                mesh.shallow_copy(mesh.translate(position_shift))
    
    def _rotate(self, angle_shift, increment=True, **kwargs):
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
        self.active = True
        for actor in self.actors:
            #shnk.actor.prop.opacity = 1 #FIXME: opacity not working for some reason
            actor.prop.color = ACTIVE_COLOR

    def make_inactive(self):
        self.active = False
        for actor in self.actors:
            #shnk.actor.prop.opacity = .2
            actor.prop.color = INACTIVE_COLOR
    
    def __del__(self):
        if self.plotter is None:
            return
        for actor in self.actors:
            self.plotter.remove_actor(actor)
    
class AbstractBaseProbe(VVASPBaseVisualizerClass):
    """Another abstract class that extends the base visualizer a bit to include some probe specific logic
    (like calculating the brain-surface entry point, computing depth, intersecting brain regions, etc.)
    
    This class can be used in conjunction with the CustomMeshObject or any other custom mesh logic defined in pyvista
    to visualize arbitrary probe geometries in the vvasp scene."""
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
        '''
        Defined in child classes, this function must set self.shank_origins to a list of shank origins
        These are used to compute the brain regions that the probe travels through.
        Can be set to None if not needed.

        Shank origins should return a [n_shanks, 3] matrix, specifying the origin of each shank
        '''
        pass

    def drive_probe_from_entry(self, ml_ap_entry, angles, depth, root_mesh=None):
        # move the probe to a specific entry point and depth
        # this is useful for driving the probe from a brain region entry point
        # and depth along the probe axis
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
        # 1. Compute the intersection point with the brain surface and update the plotter
        init_vector = (self.rotation_matrix @ INIT_VEC)
        self.intersection_vector = init_vector + self.origin
        start = self.origin.astype(np.float32)
        end = self.intersection_vector.astype(np.float32)
        points = mesh.ray_trace(start, end)[0]
        return points
    
    def compute_region_intersections(self, vvasp_atlas):
        '''Compute the brain regions that the probe travels through'''
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

    def set_location(self,origin,angles):
        super().set_location(origin,angles)
        if hasattr(self, 'root_intersection_mesh') and self.plotter is not None:
            self._update_entry_point_mesh()
            
    def move(self, direction, multiplier):
        super().move(direction, multiplier)
        if hasattr(self, 'root_intersection_mesh') and self.plotter is not None:
            self._update_entry_point_mesh()
    
    def _update_entry_point_mesh(self):
    # Move the marker of the surface intersection
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