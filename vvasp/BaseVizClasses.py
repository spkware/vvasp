from .utils import *
import pyvista as pv 
from abc import ABC, abstractmethod
import ipdb

ACTIVE_COLOR = '#FF0000'
INACTIVE_COLOR = '#000000'
SPHERE_RADIUS = 50
INIT_VEC = np.array([0, 10_000,0]) # just has to be long enough to intersect the brain surface

class VVASPBaseVisualizerClass(ABC):
    """
    An absttract base class (can not be instantiated) that will be inherited
    by child classes for visualization in vvasp. This handles the drawing and movement of meshes

    Max Melin, 2024
    """
    def __init__(self,
                 vistaplotter,
                 starting_position=(0,0,0),
                 starting_angles=(0,0,0),
                 active=True,
                 pyvista_mesh_args=None,): # a list of dicts with keyword arguments for plotter.add_mesh()
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
        self.plotter.update()

    

    def set_location(self,origin,angles):
        self._rotate(angles,increment = False)
        self._move(origin,increment = False)
                        
    def move(self, direction, multiplier):
        match direction:
            case 'left':
                position_shift = np.array([-1,0,0]) * multiplier
                self._move(position_shift)
            case 'right':
                position_shift = np.array([1,0,0]) * multiplier
                self._move(position_shift)
            case 'dorsal':
                position_shift = np.array([0,0,1]) * multiplier
                self._move(position_shift)
            case 'ventral':
                position_shift = np.array([0,0,-1]) * multiplier
                self._move(position_shift)
            case 'anterior':    
                position_shift = np.array([0,1,0]) * multiplier
                self._move(position_shift)
            case 'posterior':  
                position_shift = np.array([0,-1,0]) * multiplier
                self._move(position_shift)

            case 'tilt up': 
                angle_shift = np.array([1,0,0]) * multiplier
                self._rotate(angle_shift)
            case 'tilt down':
                angle_shift = np.array([-1,0,0]) * multiplier
                self._rotate(angle_shift)
            case 'rotate left':
                angle_shift = np.array([0,0,1]) * multiplier
                self._rotate(angle_shift)
            case 'rotate right': 
                angle_shift = np.array([0,0,-1]) * multiplier
                self._rotate(angle_shift)
            case 'spin left':
                angle_shift = np.array([0,1,0]) * multiplier
                self._rotate(angle_shift)
            case 'spin right':
                angle_shift = np.array([0,-1,0]) * multiplier
                self._rotate(angle_shift)
            
            case 'retract':
                position_shift = move3D(multiplier, *self.angles[[0,2]])
                self._move(position_shift.astype(int))
                #self.__move(position_shift)
            case 'advance':
                position_shift = -move3D(multiplier, *self.angles[[0,2]])
                self._move(position_shift.astype(int))
                #self.__move(position_shift)

            case 'home':
                self._move(np.array([0,0,0]),increment = False)
                self._rotate(np.array([-90,0,0]),increment = False)

    def _move(self, position_shift, increment=True):     
        if increment:
            self.origin += position_shift
        else:
            assert len(position_shift) == 3,ValueError('Position has to be 3 values') 
            old_position = np.array(self.origin)
            self.origin[:] = position_shift 
            position_shift = position_shift - old_position
        # move the meshes
        for i,mesh in enumerate(self.meshes):
            mesh.shallow_copy(mesh.translate(position_shift))
        self.plotter.update()
    
    def _rotate(self, angle_shift, increment=True):
        if increment:
            self.angles[:] += angle_shift
        else:
            assert len(angle_shift) == 3, ValueError('Angle has to be 3 values') 
            old_angles = np.array(self.angles)
            self.angles[:] = angle_shift 
        # rotate the meshes
        old_rotation_matrix = self.rotation_matrix
        self.rotation_matrix = rotation_matrix_from_degrees(*self.angles)
        for i,mesh in enumerate(self.meshes):
            # rotations are performed relative to the objects origin, not the origin of the pyvista scene
            # So we need to translate the mesh to the pyvista origin, rotate it, and then translate it back to its original spot
            points = old_rotation_matrix.T @ (mesh.points - self.origin).T
            mesh.points = (self.rotation_matrix @ points).T + self.origin
            mesh.shallow_copy(mesh)
        self.plotter.update()
    
    def __del__(self):
        for actor in self.actors:
            self.plotter.remove_actor(actor)
        self.plotter.update()
    
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
                 ray_trace_intersection=True,
                 vvasp_atlas=None,
                 info=None):
        self.info = info # used to save the probe properties to a file
        self.entry_point = None
        if not ray_trace_intersection or vvasp_atlas is None:
            self.ray_trace_intersection = False #if no atlas mesh is passed, we cant ray trace the insertion
        else:
            self.ray_trace_intersection = ray_trace_intersection
            self.vvasp_atlas = vvasp_atlas
            self.root_intersection_mesh = self.vvasp_atlas.meshes['root']
        self.intersection_vector = None # an imaginary line from shank origin, used for calculating the intersection with regions and the brain surface
        self.intersection_point = None

        #the following mesh and actor are used to visualize the brain surface entry point
        #they are the result of a ray trace from the probe origin to the brain surface and obey unique logic
        #thus we will handle them separately from the other meshes
        self.ball_mesh = pv.Sphere(center=np.array(starting_position).astype(np.float32), radius=SPHERE_RADIUS)
        self.ball_actor = vistaplotter.add_mesh(self.ball_mesh, color='blue')

        

        super().__init__(vistaplotter, starting_position, starting_angles, active)

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

    def drive_probe_from_entry(self, ml_ap_entry, angles, depth):
        # move the probe to a specific entry point and depth
        # this is useful for driving the probe from a brain region entry point
        # and depth along the probe axis
        if self.vvasp_atlas is None:
            raise ValueError("No atlas is defined, can not drive probe from atlas entry point")

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
    
    def __ray_trace_intersection(self):
        # 1. Compute the intersection point with the brain surface and update the plotter
        init_vector = (self.rotation_matrix @ INIT_VEC)
        self.intersection_vector = init_vector + self.origin
        start = self.origin.astype(np.float32)
        end = self.intersection_vector.astype(np.float32)
        points = self.root_intersection_mesh.ray_trace(start, end)[0]

        if points.shape[0] == 1:
            self.entry_point = points[0,:].flatten()
            self.ball_mesh.shallow_copy(pv.Sphere(center=points, radius=SPHERE_RADIUS))
        elif points.shape[0] > 1: #pick the point with the highest z value if there are multiple
            self.entry_point = points[np.argmax(points[:,2]),:].flatten()
            self.ball_mesh.shallow_copy(pv.Sphere(center=self.entry_point, radius=SPHERE_RADIUS))
        else:
            self.entry_point = None
            self.ball_mesh.shallow_copy(pv.Sphere(center=self.origin, radius=SPHERE_RADIUS))
    
    def __compute_region_intersections(self):
        # Compute the brain regions that the probe travels through
        # TODO: optionally take a channelmap
        self.region_boundary_distances = [None] * len(self.shank_origins)
        self.region_midpoint_distances = [None] * len(self.shank_origins)
        self.region_acronyms = [None] * len(self.shank_origins)

        init_vector = (self.rotation_matrix @ INIT_VEC)
        for i,shnk_origin in enumerate(self.shank_origins):
            shnk_ending = init_vector + shnk_origin
            atlas_vector = self.vvasp_atlas.bregma_positions_to_atlas_voxels([shnk_origin, shnk_ending])
            atlas_bresenham_line = bresenham3D(atlas_vector[0], atlas_vector[1]) # get the voxels that the probe passes thru 
            region_boundary_voxels, midpoint_voxels = self.vvasp_atlas.atlas_voxels_to_annotation_boundaries(atlas_bresenham_line, return_midpoints=True)
            self.region_acronyms[i] = [self.vvasp_atlas.bg_atlas.structure_from_coords(a, as_acronym=True) for a in midpoint_voxels]
            # Convert midpoints and boundaries to single distance values
            region_boundary_voxels = region_boundary_voxels * self.vvasp_atlas.bg_atlas.resolution # convert to um
            midpoint_voxels = midpoint_voxels * self.vvasp_atlas.bg_atlas.resolution
            zero_point = region_boundary_voxels[0]
            self.region_boundary_distances[i] = np.linalg.norm(region_boundary_voxels - zero_point, axis=1)
            self.region_midpoint_distances[i] = np.linalg.norm(midpoint_voxels - zero_point, axis=1)
    
    def _move(self, position_shift, increment=True):
        super()._move(position_shift, increment)
        # TODO: update the probe_origins here
        if self.ray_trace_intersection:
                self.__ray_trace_intersection()
                self.__compute_region_intersections()
        else:
            self.ball_mesh.shallow_copy(pv.Sphere(center=self.origin, radius=SPHERE_RADIUS))
        self.plotter.update()
    
    def _rotate(self, angle_shift, increment=True):
        super()._rotate(angle_shift, increment)
        # TODO: update the probe_origins here
        if self.ray_trace_intersection:
                self.__ray_trace_intersection()
                self.__compute_region_intersections()
        else:
            self.ball_mesh.shallow_copy(pv.Sphere(center=self.origin, radius=SPHERE_RADIUS))
        self.plotter.update()

    def make_active(self):
        self.active = True
        for actor in self.actors:
            #shnk.actor.prop.opacity = 1 #FIXME: opacity not working for some reason
            actor.prop.color = ACTIVE_COLOR
        self.plotter.update()

    def make_inactive(self):
        self.active = False
        for actor in self.actors:
            #shnk.actor.prop.opacity = .2
            actor.prop.color = INACTIVE_COLOR
        self.plotter.update()
    
    def xyz_locations(self, resolution=1):
        # returns a list of the brain regions that each shank (mesh) passes through
        #TODO: return the brain regions that each shank (mesh passes thru)
        # this could require ray tracing for speed, rather than an intersection
        raise NotImplementedError()
        # the following lines are from copilot, totally unteseted
        if self.entry_point is None:
            return []
        else:
            return brainglobe_atlas.get_structure_by_xyz(self.entry_point)
    
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