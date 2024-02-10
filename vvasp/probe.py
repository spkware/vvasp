from .utils import *

"""
Utility functions for visualizing probe and shank locations in 3D space.
Max Melin, 2024
"""

VAILD_PROBETYPES = {'NP24':(-410,-160,90,340),
                    'NP1(3B)':(-35,)} # the valid probetypes and a tuple with the shank offsets from the origin

ACTIVE_COLOR = '#FF0000'
INACTIVE_COLOR = '#000000'
class Shank:
    SHANK_DIMS_UM = np.array([70,-10_000,10]) # the dimensions of the shank in um
    def __init__(self, vistaplotter, tip, angles, active=True):
        self.plotter = vistaplotter
        self.tip = tip # [ML,AP,DV], the corner of the shank, used for drawing the shank
        self.angles = angles # [elev, spin, yaw], the angles of the shank in degrees
        self.mesh = None
        self.define_vectors_for_rectangle()
        self.plot_new_shank_mesh()

    def define_vectors_for_rectangle(self):
        shank_vectors = np.array([[Shank.SHANK_DIMS_UM[0],Shank.SHANK_DIMS_UM[1],0], #the orthogonal set of vectors used to define a rectangle, these will be translated and rotated about the tip
                                  [Shank.SHANK_DIMS_UM[0],0,0],
                                  [0,0,Shank.SHANK_DIMS_UM[2]]]).T
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

    def move(self, position_shift):
        self.tip += position_shift
        self.shank_vectors += position_shift
        self.update_mesh()
        #self.define_vectors_for_rectangle()
        #self.plotter.remove_actor(self.actor) # for now, removing the actor and adding a new one is the only way to move the shank
        #self.actor = self.plotter.add_mesh(self.mesh,color=ACTIVE_COLOR,opacity = 1,line_width=3)
    
class Probe:
    def __init__(self, vistaplotter, probetype, origin, angles, active=True):
        assert probetype in VAILD_PROBETYPES.keys(), f'Invalid probetype: {probetype}'
        self.plotter = vistaplotter
        self.probetype = probetype
        self.active = active
        self.origin = np.array(origin) # the "true center" of the probe tip, [ML,AP,DV]
        angles = np.array(angles)
        angles[2] = -angles[2] # rotation about z is inverted for probes
        angles[0] = -angles[0] # rotation about x is inverted for probes
        self.angles = angles
        self.shanks = []
        self.__add_shanks()

    def make_active(self):
        self.active = True
        for shnk in self.shanks:
            #shnk.actor.prop.opacity = 1 #FIXME: opacity not working for some reason
            shnk.actor.prop.color = ACTIVE_COLOR

    def make_inactive(self):
        self.active = False
        for shnk in self.shanks:
            #shnk.actor.prop.opacity = .2
            shnk.actor.prop.color = INACTIVE_COLOR

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
            case 'right':
                position_shift = np.array([1,0,0]) * multiplier
            case 'dorsal':
                position_shift = np.array([0,0,1]) * multiplier
            case 'ventral':
                position_shift = np.array([0,0,-1]) * multiplier
            case 'anterior':    
                position_shift = np.array([0,1,0]) * multiplier
            case 'posterior':  
                position_shift = np.array([0,-1,0]) * multiplier
    
        self.__move(position_shift)
    
    def __move(self, position_shift):     
        self.origin += position_shift
        for shnk in self.shanks:
            shnk.move(position_shift)
