from . import io
from .utils import *

def list_availible_atlases():
    return [x.name for x in io.ATLAS_DIR.glob('*')]

class Atlas:
    def __init__(self, vistaplotter, atlas_name=None, structure_tree_depth=3):
        if atlas_name is None:
            atlas_name = io.preferences['atlas']
        self.name = atlas_name
        self.plotter = vistaplotter
        self.visible_region_actors = {}
        self.meshes = {}
        self.meshcols = {}
        self.fetch_atlas()
        self.load_atlas_metadata(structure_tree_depth)
        self.initialize()
        
    def fetch_atlas(self):
        #download the atlas if not present
        pass

    def load_atlas_metadata(self, structure_tree_depth):
        atlas_path = io.ATLAS_DIR / io.preferences['atlas']
        global structures
        with open(atlas_path/'structures.json','r') as fd:
            structures = io.json.load(fd)
        global metadata
        with open(atlas_path/'metadata.json','r') as fd:
            metadata = io.json.load(fd)
        maxdepth = np.max([len(p['structure_id_path']) for p in structures]) #get max tree depth
        structures = [s for s in structures if len(s['structure_id_path']) <= structure_tree_depth] #restrict to regions at or below max tree depth

        self.structures = pd.DataFrame(structures)    
        self.structure_tree_depth = structure_tree_depth
        self.maxdepth = maxdepth
        self.atlas_path = atlas_path
        self.bregma_location = np.array(io.preferences['bregma_locations'][self.name])*metadata['resolution']
        self.metadata = metadata

    def initialize(self, show_root=True, show_bregma=True):
        # load up meshes, rotate/translate them appropriately and compute the areas they occupy in space. 
        # Importantly, don't render them to the plotter yet, it will just bog it down.
        regions = list(self.structures.acronym.values)
        axes = io.pv.Axes()
        axes.origin = self.bregma_location
        
        rotate5deg = True


        for r in regions:
            try:
                s = io.load_structure_mesh(self.atlas_path, self.structures, r) 
            except:
                print(f'Failed to load mesh {r}')
                self.structures = self.structures[self.structures.acronym != r]
                continue
        
            s[0].rotate_y(90, point=axes.origin, inplace=True) # rotate the meshes so that [x,y,z] => [ML,AP,DV]
            s[0].rotate_x(-90, point=axes.origin, inplace=True)
            if rotate5deg:
                s[0].rotate_x(5,point=axes.origin, inplace=True) # allenCCF has a 5 degree tilt
            s[0].translate(-self.bregma_location, inplace=True) #make bregma the origin
            self.meshes[r] = s[0]
            self.meshcols[r] = s[1]['rgb_triplet']
        assert len(self.meshes) == len(self.structures)

        if show_root:
            self.root_actor = self.plotter.add_mesh(self.meshes['root'],
                                  color=self.meshcols['root'],
                                  opacity=0.08,
                                  silhouette=False,
                                  name='root')
        if show_bregma:
            self.bregma_actor = self.plotter.add_mesh(io.pv.Sphere(radius=100, center=(0,0,0)))

    def add_atlas_region_mesh(self, region_acronym):
        if region_acronym in self.visible_region_actors.keys():
            return #don't replot the same region
        actor = self.plotter.add_mesh(self.meshes[region_acronym], #make bregma the origin
                              color=self.meshcols[region_acronym],
                              opacity = 0.7,
                              render=False,
                              silhouette=False)
        self.visible_region_actors.update({region_acronym: actor})
    
    def remove_atlas_region_mesh(self, region_acronym):
        if region_acronym in self.visible_region_actors.keys():
            self.plotter.remove_actor(self.visible_region_actors[region_acronym])
            self.visible_region_actors.pop(region_acronym)
        else:
            print(f'No region {region_acronym} to remove')
    
    def clear_atlas(self):
        for region in self.visible_region_actors:
            self.remove_atlas_region_mesh(region)
        self.visible_region_actors = {}

    def map_location_to_atlas_region(self, locations):
        # map an array of locations to the atlas regions they lie within
        # can pass the points coming from the probe origin here, can also find ones passing through root to compute the 
        # position where the probe exits the skull
        raise NotImplementedError()

    @property
    def atlas_properties(self):
        return dict(name=self.name, visible_regions=list(self.visible_region_actors.keys()))

    def __del__(self):
        temp = list(self.visible_region_actors.keys())
        for region in temp:
            self.remove_atlas_region_mesh(region)
        self.plotter.remove_actor(self.root_actor)
        self.plotter.remove_actor(self.bregma_actor)
        self.plotter.update()
        