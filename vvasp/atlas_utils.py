from . import io
import pandas as pd
import numpy as np


def list_availible_atlases():
    return [x.name for x in io.ATLAS_DIR.glob('*')]

class Atlas:
    def __init__(self, vistaplotter, atlas_name=None):
        if atlas_name is None:
            atlas_name = io.preferences['atlas']
        self.name = atlas_name
        self.plotter = vistaplotter
        self.visible_regions = []
        self.fetch_atlas()
        self.load_atlas()


    def fetch_atlas(self):
        #download the atlas if not present
        pass

    def load_atlas(self):
        atlas_path = io.ATLAS_DIR / io.preferences['atlas']
        global structures
        with open(atlas_path/'structures.json','r') as fd:
            structures = io.json.load(fd)
        global metadata
        with open(atlas_path/'metadata.json','r') as fd:
            metadata = io.json.load(fd)

        self.structures = pd.DataFrame(structures)    
        self.atlas_path = atlas_path
        self.bregma_location = np.array(io.preferences['bregma_locations'][self.name])*metadata['resolution']
        self.metadata = metadata

    def add_atlas_region_mesh(self, region_acronym):
        if region_acronym in self.visible_regions:
            return #don't replot the same region
        axes = io.pv.Axes()
        axes.origin = self.bregma_location

        s = io.load_structure_mesh(self.atlas_path, self.structures, region_acronym)

        rotate5deg = True

        s[0].rotate_y(90, point=axes.origin, inplace=True) # rotate the meshes so that [x,y,z] => [ML,AP,DV]
        s[0].rotate_x(-90, point=axes.origin, inplace=True)
        if rotate5deg:
            #FIXME: is the following line positive or negative?
            s[0].rotate_x(-5,point=axes.origin, inplace=True) # allenCCF has a 5 degree tilt
        if s[1].acronym == 'root':
            self.plotter.add_mesh(s[0].translate(-self.bregma_location), #make bregma the origin
                       color = s[1]['rgb_triplet'],
                       opacity = 0.1,silhouette=False)
        else:
            self.plotter.add_mesh(s[0].translate(-self.bregma_location), #make bregma the origin
                       color=s[1]['rgb_triplet'],
                       opacity = 0.7,
                       silhouette=dict(color='#000000',line_width=1))
        self.visible_regions.append(region_acronym)