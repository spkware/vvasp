from .utils import *
import pyvista as pv

"""
Utility functions for visualizing probe and shank locations in 3D space.
Max Melin, 2024
"""

VAILD_PROBETYPES = {'NP24':(-410,-160,90,340),
                    'NP1(3B)':(-35,)} # the valid probetypes and a tuple with the shank offsets from the origin
class Shank:
    SHANK_DIMS_UM = np.array([70,-10_000,10]) # the dimensions of the shank in um
    def __init__(self, vistaplotter, tip, angles, active=True):
        self.plotter = vistaplotter
        self.tip = tip # [ML,AP,DV], the corner of the shank, used for drawing the shank
        self.angles = angles # [elev, spin, yaw], the angles of the shank in degrees
        self.__define_vectors_for_rectangle()
        self.plot_new_shank_mesh()

    def __define_vectors_for_rectangle(self):
        shank_vectors = np.array([[Shank.SHANK_DIMS_UM[0],Shank.SHANK_DIMS_UM[1],0], #the orthogonal set of vectors used to define a rectangle, these will be translated and rotated about the tip
                                  [Shank.SHANK_DIMS_UM[0],0,0],
                                  [0,0,Shank.SHANK_DIMS_UM[2]]]).T
        rotation_matrix = rotation_matrix_from_degrees(*self.angles)
        self.tip = (rotation_matrix @ self.tip) #rotate the tip of the shanks
        shank_vectors =  (rotation_matrix @ shank_vectors).T #rotate the shank vectors by probe angles
        shank_vectors += self.tip #translate the shank vectors to the tip of the shanks
        self.shank_vectors = shank_vectors
    
    @property
    def mesh(self):
        return pv.Rectangle(self.shank_vectors)
    
    def plot_new_shank_mesh(self):
        self.actor = self.plotter.add_mesh(self.mesh,color='#000000',opacity = 1,line_width=3)
    
class Probe:
    def __init__(self, vistaplotter, probetype, origin, angles, active=True):
        assert probetype in VAILD_PROBETYPES.keys(), f'Invalid probetype: {probetype}'
        self.plotter = vistaplotter
        self.probetype = probetype
        self.active = active
        self.origin = origin # the "true center" of the probe tip, [ML,AP,DV]
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
            shnk.actor.prop.color = 'red'

    def make_inactive(self):
        self.active = False
        for shnk in self.shanks:
            #shnk.actor.prop.opacity = .2
            shnk.actor.prop.color = 'black'

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
