from .utils import *
import pyvista as pv 
from abc import ABC, abstractmethod

# TODO: make the gui build the probe control buttons based on probe_attributes keys or something. 
# That way they can be different

class NewscaleMPM():
    pass


class ManipulatorMixin(ABC):
    '''
    This mixin class should provide some way to change the coordinate system of a probe, so that it's 
    manipulated along a different origin/degrees of freedom.
    '''

##### Specific implementations of different ManipulatorMixin classes #######
class NewscaleMPMObject(ManipulatorMixin):
    def __init__(self):
        super().__init__()