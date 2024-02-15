from .utils import *

"""
Utility functions for visualizing probe and shank locations in 3D space.
Max Melin, 2024
"""

VAILD_PROBETYPES = {'NP24':(-410,-160,90,340),
                    'NP1(3B)':(-35,)} # the valid probetypes and a tuple with the shank offsets from the origin

SHANK_DIMS_UM = np.array([70,-10_000,0]) # the dimensions of the shank in um
INIT_VEC = np.array([0,SHANK_DIMS_UM[1],0])
SPHERE_RADIUS = 50

ACTIVE_COLOR = '#FF0000'
INACTIVE_COLOR = '#000000'

class Shank:
    def __init__(self, vistaplotter, tip, angles, active=True):
        self.plotter = vistaplotter
        self.tip = tip # [ML,AP,DV], the corner of the shank, used for drawing the shank
        self.angles = angles # [elev, spin, yaw], the angles of the shank in degrees
        self.mesh = None
        self.shank_vectors = None
        self.define_vectors_for_rectangle()
        self.plot_new_shank_mesh()

    def define_vectors_for_rectangle(self):
        shank_vectors = np.array([[SHANK_DIMS_UM[0],SHANK_DIMS_UM[1],0], #the orthogonal set of vectors used to define a rectangle, these will be translated and rotated about the tip
                                  [SHANK_DIMS_UM[0],0,0],
                                  [0,0,SHANK_DIMS_UM[2]]]).T
        rotation_matrix = rotation_matrix_from_degrees(*self.angles)
        self.tip = (rotation_matrix @ self.tip) #rotate the tip of the shanks
        shank_vectors =  (rotation_matrix @ shank_vectors).T #rotate the shank vectors by probe angles
        shank_vectors += self.tip #translate the shank vectors to the tip of the shanks
        self.shank_vectors = shank_vectors
        self.update_mesh()
    
    def update_mesh(self):
        #self.mesh = pv.Rectangle(self.shank_vectors)
        if self.mesh is not None:
            self.mesh.shallow_copy(pv.Rectangle(self.shank_vectors)) #update the mesh
        else:
            self.mesh = pv.Rectangle(self.shank_vectors) #create the mesh for the first time
        self.plotter.update()
    
    
    def plot_new_shank_mesh(self):
        self.actor = self.plotter.add_mesh(self.mesh,color=ACTIVE_COLOR ,opacity = 1,line_width=3)

class Probe:
    def __init__(self, vistaplotter, probetype, origin, angles, active=True, ray_trace_insertion=True, atlas_root_mesh=None):
        assert probetype in VAILD_PROBETYPES.keys(), f'Invalid probetype: {probetype}'
        if ray_trace_insertion and atlas_root_mesh is None:
            self.ray_trace_insertion = False #if no atlas mesh is passed, we cant ray trace the insertion
        else:
            self.ray_trace_insertion = ray_trace_insertion
        self.plotter = vistaplotter
        self.probetype = probetype
        self.active = active
        self.origin = np.array(origin) # the "true center" of the probe tip, [ML,AP,DV]
        angles = np.array(angles)
        #angles[2] = -angles[2] # rotation about z is inverted for probes
        #angles[0] = -angles[0] # rotation about x is inverted for probes
        self.angles = angles
        self.rotation_matrix = rotation_matrix_from_degrees(*self.angles)
        self.shanks = []
        self.intersection_vector = None # an imaginary line from shank origin, used for calculating the intersection with brain surface
        self.__add_shanks()
        self.atlas_root_mesh = atlas_root_mesh.triangulate()
        self.entry_point = None
        if atlas_root_mesh is not None and self.ray_trace_insertion: #if passing an atlas mesh, ray trace the intersection with the brain surface
            self.surface_entry_mesh = pv.Sphere(center=self.origin.astype(np.float32), radius=SPHERE_RADIUS)
            self.plotter.add_mesh(self.surface_entry_mesh, color='blue', name='surface_entry')
        self.__move(np.array([0,0,0])) # just use this to update the mesh location
        if active:
            self.make_active()
        else:
            self.make_inactive()

    @property
    def probe_properties(self):
        return dict(probetype=self.probetype,
                    origin=self.origin.tolist(),
                    angles=self.angles.tolist(),
                    active=self.active)
    
    def __ray_trace_intersection(self):
        init_vector = (self.rotation_matrix @ INIT_VEC)
        self.intersection_vector = init_vector + self.origin
        start = self.origin.astype(np.float32)
        end = self.intersection_vector.astype(np.float32)
        points = self.atlas_root_mesh.ray_trace(start, end)[0]

        if points.shape[0] == 1:
            self.entry_point = points
            self.surface_entry_mesh.shallow_copy(pv.Sphere(center=points, radius=SPHERE_RADIUS))
        elif points.shape[0] > 1: #pick the point with the highest z value if there are multiple
            self.entry_point = points[np.argmax(points[:,2])]
            self.surface_entry_mesh.shallow_copy(pv.Sphere(center=self.entry_point, radius=SPHERE_RADIUS))
        else:
            self.entry_point = None
            self.surface_entry_mesh.shallow_copy(pv.Sphere(self.origin, radius=SPHERE_RADIUS))

    def make_active(self):
        self.active = True
        for shnk in self.shanks:
            #shnk.actor.prop.opacity = 1 #FIXME: opacity not working for some reason
            shnk.actor.prop.color = ACTIVE_COLOR
            self.plotter.update()

    def make_inactive(self):
        self.active = False
        for shnk in self.shanks:
            #shnk.actor.prop.opacity = .2
            shnk.actor.prop.color = INACTIVE_COLOR
            self.plotter.update()

    def __add_shanks(self):
        for offset in VAILD_PROBETYPES[self.probetype]:
            tip = np.array([offset,0,0])
            shnk = Shank(self.plotter, tip+self.origin, self.angles, self.active)
            shnk.shank_vectors += self.origin #move the shank to the origin of the probe (after rotation of individual shanks is already applied)
            self.shanks.append(shnk)

    @property
    def shank_meshes(self):
        return [shnk.mesh for shnk in self.shanks]

    @property
    def shank_actors(self):
        return [shnk.actor for shnk in self.shanks]

    def move(self, direction, multiplier):
        match direction:
            case 'left':
                position_shift = np.array([-1,0,0]) * multiplier
                self.__move(position_shift)
            case 'right':
                position_shift = np.array([1,0,0]) * multiplier
                self.__move(position_shift)
            case 'dorsal':
                position_shift = np.array([0,0,1]) * multiplier
                self.__move(position_shift)
            case 'ventral':
                position_shift = np.array([0,0,-1]) * multiplier
                self.__move(position_shift)
            case 'anterior':    
                position_shift = np.array([0,1,0]) * multiplier
                self.__move(position_shift)
            case 'posterior':  
                position_shift = np.array([0,-1,0]) * multiplier
                self.__move(position_shift)

            case 'tilt up': 
                angle_shift = np.array([1,0,0]) * multiplier
                self.__rotate(angle_shift)
            case 'tilt down':
                angle_shift = np.array([-1,0,0]) * multiplier
                self.__rotate(angle_shift)
            case 'rotate left':
                angle_shift = np.array([0,0,1]) * multiplier
                self.__rotate(angle_shift)
            case 'rotate right': 
                angle_shift = np.array([0,0,-1]) * multiplier
                self.__rotate(angle_shift)
            case 'spin left':
                angle_shift = np.array([0,-1,0]) * multiplier
                self.__rotate(angle_shift)
            case 'spin right':
                angle_shift = np.array([0,1,0]) * multiplier
                self.__rotate(angle_shift)
            
            case 'retract':
                position_shift = -move3D(multiplier, *self.angles[[0,2]])
                self.__move(position_shift.astype(np.int))
                #self.__move(position_shift)
            case 'advance':
                position_shift = move3D(multiplier, *self.angles[[0,2]])
                self.__move(position_shift.astype(np.int))
                #self.__move(position_shift)
    

    def __move(self, position_shift):     
        self.origin += position_shift
        for shnk,offset in zip(self.shanks, VAILD_PROBETYPES[self.probetype]):
            tip = np.array([offset,0,0])
            shnk.tip = tip
            #shnk.angles += angle_shift #Probe.shanks[:].angles all point to Probe.angles, so no need to modify the shank angles
            shnk.define_vectors_for_rectangle()
            shnk.shank_vectors += self.origin
            shnk.update_mesh()
            if self.atlas_root_mesh is not None and self.ray_trace_insertion:
                self.__ray_trace_intersection()

    def __rotate(self, angle_shift):
        self.angles += angle_shift
        for shnk,offset in zip(self.shanks, VAILD_PROBETYPES[self.probetype]):
            tip = np.array([offset,0,0])
            shnk.tip = tip
            #shnk.angles += angle_shift #Probe.shanks[:].angles all point to Probe.angles, so no need to modify the shank angles
            shnk.define_vectors_for_rectangle()
            shnk.shank_vectors += self.origin
            shnk.update_mesh()

        self.rotation_matrix = rotation_matrix_from_degrees(*self.angles)
        if self.atlas_root_mesh is not None and self.ray_trace_insertion:
            self.__ray_trace_intersection()
    
    def __del__(self):
        for shnk in self.shanks:
            self.plotter.remove_actor(shnk.actor)
        self.plotter.remove_actor(self.plotter.actors['surface_entry'])
        self.plotter.update()