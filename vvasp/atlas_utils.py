from . import io
from .utils import *
from tifffile import imread

def list_availible_atlases():
    return [x.name for x in io.ATLAS_DIR.glob('*')]

class VVASPAtlas:
    ''' 
    Wraps the brainglobe atlas (bg_atlas) to provide funcitonality for showing and hiding meshes
    '''
    def __init__(self, vistaplotter, atlas_name=None, min_tree_depth=3, max_tree_depth=7):
        if atlas_name is None:
            atlas_name = io.preferences['default_atlas']
        self.name = atlas_name
        self.plotter = vistaplotter
        self.visible_region_actors = {}
        self.meshes = {}
        self.meshcols = {}
        self.fetch_atlas(atlas_name)
        self.load_atlas_metadata(min_tree_depth, max_tree_depth)
        self.initialize()
        
    def fetch_atlas(self, force_redownload=False):
        from brainglobe_atlasapi import BrainGlobeAtlas, show_atlases
        #download the atlas if not present
        bg_atlas = BrainGlobeAtlas(self.name, check_latest=False)
        self.bg_atlas = bg_atlas
        self.atlas_path = bg_atlas.brainglobe_dir / bg_atlas.local_full_name
        #show_atlases() # show all available atlases from BrainGlobe

    def load_atlas_metadata(self, min_tree_depth, max_tree_depth):
        #TODO: maybe use some brainglobe functionality to load data and traverse tree depths instead
        with open(self.atlas_path/'structures.json','r') as fd:
            structures = io.json.load(fd)
        with open(self.atlas_path/'metadata.json','r') as fd:
            metadata = io.json.load(fd)
        maxdepth = np.max([len(p['structure_id_path']) for p in structures]) #get max tree depth
        tmp_root = [s for s in structures if s['acronym'] == 'root'][0]
        structures = [s for s in structures if len(s['structure_id_path']) <= max_tree_depth] #restrict to regions at or below max tree depth
        structures = [s for s in structures if len(s['structure_id_path']) >= min_tree_depth] #restrict to regions at or below max tree depth
        structures.append(tmp_root) #add root back in (it can get removed if min_tree_depth > 1)
        structures = pd.DataFrame(structures)
        self.structures = pd.DataFrame(structures)    
        self.min_tree_depth = min_tree_depth
        self.max_tree_depth = max_tree_depth
        self.maxdepth = maxdepth
        self.bregma_location = np.array(io.preferences['atlas_transformations'][self.name]['bregma_location'])*metadata['resolution']
        print(self.bregma_location, flush=True)
        self.metadata = metadata

    def initialize(self, show_root=True, show_bregma=True):
        # load up meshes, rotate/translate them appropriately and compute the areas they occupy in space. 
        # Importantly, don't render them to the plotter yet, it will just bog it down.
        regions = list(self.structures.acronym.values)
        axes = io.pv.Axes()
        #axes.origin = self.bregma_location
        axes.origin = np.array([0,0,0])
        for r in regions:
            try:
                s = io.load_structure_mesh(self.atlas_path, self.structures, r) 
            except:
                print(f'Failed to load mesh {r}')
                self.structures = self.structures[self.structures.acronym != r]
                continue
        
            s[0].translate(-self.bregma_location, inplace=True) #make bregma the origin
            self.rotation_angles = -np.array(io.preferences['atlas_transformations'][self.name]['angles'])
            s[0].rotate_x(self.rotation_angles[0], point=axes.origin, inplace=True)
            s[0].rotate_y(self.rotation_angles[1], point=axes.origin, inplace=True) # rotate the meshes so that [x,y,z] => [ML,AP,DV]
            s[0].rotate_z(self.rotation_angles[2], point=axes.origin, inplace=True) # rotate the meshes so that [x,y,z] => [ML,AP,DV]
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

        r_angles = -self.rotation_angles
        self.rotmat = rotation_matrix_from_degrees(*r_angles, order='zyx') # used to get the annotations

        self.annotations = imread(self.atlas_path/'annotation.tiff')

    def bregma_positions_to_structures(self, positions_um):
        voxels = self.bregma_positions_to_atlas_voxels(positions_um)
        region_acronyms = [self.bg_atlas.structure_from_coords(a, as_acronym=True) for a in voxels]
        return region_acronyms

    def bregma_positions_to_atlas_voxels(self, positions_um):
        positions_um = np.dot(positions_um, self.rotmat.T)
        positions_um = positions_um + self.bregma_location
        voxels = np.array(np.round(positions_um / self.bg_atlas.metadata['resolution'])).astype(int)
        voxels = np.clip(voxels, 0, np.array(self.bg_atlas.annotation.shape)-1)
        return voxels

    def atlas_voxels_to_annotation_boundaries(self,bresenham_line):
        '''
        Uses a bresenham line to compute the atlas voxels where the line intersects the boundaries between regions.
        '''
        bresenham_line = np.clip(bresenham_line, 0, np.array(self.annotations.shape) - 1)
        region_ids = self.annotations[tuple(bresenham_line.T)]
        region_boundaries = bresenham_line[np.where(np.diff(region_ids) != 0)]
        return region_boundaries

    def add_atlas_region_mesh(self, region_acronym, side='both', force_replot=False, **pv_kwargs):
        if region_acronym in self.visible_region_actors.keys() and not force_replot:
            return #don't replot the same region
        m = self.meshes[region_acronym]
        if side=='left':
            m = m.clip(origin=(0,0,0), normal=(-1,0,0), invert=False, inplace=False)
        elif side=='right':
            m = m.clip(origin=(0,0,0), normal=(1,0,0), invert=False, inplace=False)
        elif side=='both':
            pass
        else:
            raise ValueError(f'Invalid side {side}')
        actor = self.plotter.add_mesh(m,
                              color=self.meshcols[region_acronym],
                              opacity = 0.7,
                              render=False,
                              silhouette=False,
                              **pv_kwargs)
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
        return dict(name=self.name,
                    min_tree_depth=self.min_tree_depth,
                    max_tree_depth=self.max_tree_depth,
                    visible_regions=self.visible_atlas_regions)
    
    @property
    def visible_atlas_regions(self):
        return list(self.visible_region_actors.keys())
    
    @property
    def all_atlas_regions(self):
        return self.structures.acronym.values

    def __del__(self):
        temp = list(self.visible_region_actors.keys())
        for region in temp:
            self.remove_atlas_region_mesh(region)
        self.plotter.remove_actor(self.root_actor)
        self.plotter.remove_actor(self.bregma_actor)
        self.plotter.update()
        
