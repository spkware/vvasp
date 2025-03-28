from . import io
from tqdm import tqdm
from .utils import *
from functools import cached_property
import matplotlib.pyplot as plt

def list_availible_atlases():
    return [x.name for x in io.ATLAS_DIR.glob('*')]

SLICE_TO_BG_SPACE = dict(coronal='frontal',
                         sagittal='sagittal',
                         transverse='horizontal')

MLAPDV_SLICE_TO_INDEX = dict(sagittal=0, coronal=1, transverse=2)

class VVASPAtlas:
    ''' 
    The VVASPAtlas wraps the brainglobe atlas object (self.bg_atlas) to provide the following funcitonality:

    1. Manages mapping of sub-regions to their parents (one might not necessarily need the full parcellation of an atlas).
    2. Transforms between bregma space (ml, ap, dv) and atlas space (voxels), agnostic to the coordinate system of the atlas used.
    3. Compute the path of a probe or other object through the atlas and get the regions it traverses.
    4. Provides a simple interface to plot regions of the atlas in 3D using pyvista, the meshes are all automatically transformed from the atlas space to the bregma anatomical space.
    5. Provides an interface to plot 2D slices of the atlas annotation volume.
    '''
    def __init__(self, vistaplotter=None, atlas_name=None, show_root=True, show_bregma=True, mapping='Beryl', min_tree_depth=None, max_tree_depth=None):
        if mapping is None:
            min_tree_depth = 1
            max_tree_depth = 10
        if vistaplotter is None:
            vistaplotter = io.pv.Plotter()
        if atlas_name is None:
            atlas_name = io.preferences['default_atlas']
        self.name = atlas_name
        self.plotter = vistaplotter
        self.visible_region_actors = {}
        self.meshes = {}
        self.meshcols = {}
        self.show_root = show_root
        self.show_bregma = show_bregma
        self.fetch_atlas(atlas_name)
        self.load_atlas_metadata(mapping, min_tree_depth, max_tree_depth)
        self.initialize()
        
    def fetch_atlas(self, force_redownload=False):
        from brainglobe_atlasapi import BrainGlobeAtlas, show_atlases
        #download the atlas if not present
        bg_atlas = BrainGlobeAtlas(self.name, check_latest=False)
        self.bg_atlas = bg_atlas
        self.atlas_path = bg_atlas.brainglobe_dir / bg_atlas.local_full_name
        #show_atlases() # show all available atlases from BrainGlobe

    def load_atlas_metadata(self, mapping='Beryl', min_tree_depth=None, max_tree_depth=None):
        #TODO: maybe use some brainglobe functionality to load data and traverse tree depths instead
        with open(self.atlas_path/'structures.json','r') as fd:
            structures = io.json.load(fd)
        with open(self.atlas_path/'metadata.json','r') as fd:
            metadata = io.json.load(fd)
        temp = pd.DataFrame(structures)
        self.colormap = temp[['acronym','rgb_triplet']].set_index('acronym').to_dict()['rgb_triplet']
        self.colormap['Outside atlas'] = [0,0,0] # manually add this
        tmp_root = [s for s in structures if s['acronym'] == 'root'][0]
        if min_tree_depth is not None and max_tree_depth is not None and mapping is None:
            structures = [s for s in structures if len(s['structure_id_path']) <= max_tree_depth] #restrict to regions at or below max tree depth
            structures = [s for s in structures if len(s['structure_id_path']) >= min_tree_depth] #restrict to regions at or below max tree depth
        elif mapping is not None and min_tree_depth is None and max_tree_depth is None:
            mapping_file = Path(__file__).parent.parent / 'assets' / f'{mapping}.csv'
            mapping_structures = pd.read_csv(mapping_file)['acronym'].values
            structures = [s for s in structures if s['acronym'] in mapping_structures]
            self.mapping_structures = mapping_structures
        else:
            raise ValueError('Must specify either min_tree_depth and max_tree_depth or mapping, not both.')
        if min_tree_depth is None:
            structures.append(tmp_root) #add root back in
        elif min_tree_depth > 1:
            structures.append(tmp_root) #add root back in (it can get removed if min_tree_depth > 1)
        # TODO: don't put root back in?
        structures = pd.DataFrame(structures)
        self.structures = pd.DataFrame(structures)    
        self.min_tree_depth = min_tree_depth
        self.max_tree_depth = max_tree_depth
        self.mapping = mapping
        self.bregma_location = np.array(io.preferences['atlas_transformations'][self.name]['bregma_location'])*metadata['resolution']
        self.metadata = metadata

    def initialize(self):
        # load up meshes, rotate/translate them appropriately and compute the areas they occupy in space. 
        # Importantly, don't render them to the plotter yet, it will just bog it down.
        regions = list(self.structures.acronym.values)
        axes = io.pv.Axes()
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

        if self.show_root and self.plotter is not None:
            self.root_actor = self.plotter.add_mesh(self.meshes['root'],
                                  color=self.meshcols['root'],
                                  opacity=0.08,
                                  silhouette=False,
                                  name='root')
        if self.show_bregma and self.plotter is not None:
            self.bregma_actor = self.plotter.add_mesh(io.pv.Sphere(radius=100, center=(0,0,0)))

        self.rotmat = rotation_matrix_from_degrees(*self.rotation_angles, order='xyz') # used to get the annotations

    def bregma_positions_to_structures(self, positions_um):
        voxels = self.bregma_positions_to_atlas_voxels(positions_um)
        region_acronyms = [self.bg_atlas.structure_from_coords(a, as_acronym=True) for a in voxels]
        return region_acronyms

    def bregma_positions_to_atlas_voxels(self, mlapdv_positions_um):
        mlapdv_positions_um = np.dot(mlapdv_positions_um, self.rotmat)
        mlapdv_positions_um = mlapdv_positions_um + self.bregma_location
        voxels = np.array(np.round(mlapdv_positions_um / self.bg_atlas.metadata['resolution'])).astype(int)
        #voxels = np.clip(voxels, 0, np.array(self.bg_atlas.annotation.shape)-1)
        return voxels
    
    def atlas_voxels_to_bregma_positions(self, voxels):
        positions_um = np.array(voxels) * self.bg_atlas.metadata['resolution']
        positions_um = positions_um - self.bregma_location
        positions_um = np.dot(positions_um, np.linalg.inv(self.rotmat))
        return positions_um

    def atlas_voxels_to_annotation_boundaries(self,bresenham_line, return_midpoints=False):
        '''
        Uses a bresenham line to compute the atlas voxels where the line intersects the boundaries between regions.
        If return_midpoints is True, also return the midpoints between the region boundaries.
        '''
        bresenham_line = np.clip(bresenham_line, 0, np.array(self.bg_atlas.annotation.shape) - 1)
        region_ids = self.bg_atlas.annotation[tuple(bresenham_line.T)]
        region_boundaries = bresenham_line[np.where(np.diff(region_ids) != 0)]
        region_boundaries = np.vstack([bresenham_line[0], region_boundaries, bresenham_line[-1]])
        if not return_midpoints:
            return region_boundaries
        else:
            if region_boundaries.shape[0] == 0:
                midpoints = np.empty((0,3))
            else:
                #temp = np.vstack([bresenham_line[0], region_boundaries, bresenham_line[-1]])
                midpoints = ((region_boundaries[:-1] + region_boundaries[1:]) / 2).astype(int)
            return region_boundaries, midpoints

    def show_all_regions(self, side='both', add_root=False, **pv_kwargs):
        for r in self.structures.acronym:
            if r == 'root' and not add_root:
                continue
            self.add_atlas_region_mesh(r, side=side, force_replot=False, **pv_kwargs)

    def add_atlas_region_mesh(self, region_acronym, side='both', force_replot=False, **pv_kwargs):
        PV_KWARG_DEFAULTS = dict(opacity=.7,
                                 render=False,
                                 silhouette=False) 
        # update user kwargs with defaults if they dont exist
        for k in PV_KWARG_DEFAULTS.keys():
            if k not in pv_kwargs.keys():
                pv_kwargs[k] = PV_KWARG_DEFAULTS[k]

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
    
    ##################################
    ##### 2D slicing and plotting functions ######
    ##################################

    def plot_2d_slice(self, slice_plane, slice_location_um, ax=None):
        """
        Plot a 2D slice from the atlas annotation volume at a given location and plane.
        Options for slice plane are 'coronal', 'sagittal', 'transverse'.
        slice_location_um is the location of the slice in micrometers (relative to bregma).
        The remapped annotation is returned by default, if return_full_annotation is set to True, the full annotation volume is returned.

        Parameters
        ----------
        slice_plane : string, {'coronal', 'sagittal', 'transverse'}
            Defines the axis to slice along
        slice_location_um : float, int
            Defines the location of the slice in micrometers (relative to bregma).
        ax : matplotlib.axes.Axes, optional
            a matplotlib to plot on, by default None

        Returns
        -------
        fig, ax
            matplotlib figure and axes objects
        """        
        if ax is None:
            fig, ax = plt.subplots()
        slc = self.get_2d_slice(slice_plane, slice_location_um)
        colored_slice = np.ones((slc.shape[0], slc.shape[1], 3)).astype(int) * 255 # make background white
        unique_ids = np.unique(slc)
        unique_ids = unique_ids[unique_ids != 0] # need to drop the 0 value (background)
        for id in unique_ids:
            color = self.bg_atlas.structures[id]['rgb_triplet']
            colored_slice[slc == id] = color
        ax.imshow(colored_slice)
        return fig, ax
    
    def get_2d_slice(self,slice_plane, slice_location_um, return_full_annotation=False):
        '''
        Get a 2D slice from the atlas annotation volume at a given location and plane.
        Options for slice plane are 'coronal', 'sagittal', 'transverse'.
        slice_location_um is the location of the slice in micrometers (relative to bregma).
        The remapped annotation is returned by default, if return_full_annotation is set to True, the full annotation volume is returned.
        '''
        assert slice_plane in SLICE_TO_BG_SPACE.keys(), f"Invalid slice plane, must be one of {SLICE_TO_BG_SPACE.keys()}"

        # use brainglobe space definition to ensure consistency across atlases, this finds the proper axis to slice along
        slicing_index = self.bg_atlas.space.sections.index(SLICE_TO_BG_SPACE[slice_plane]) 

        # Convert the slice location to atlas voxel coordinates (transform from bregma space to atlas space)
        slice_location_um_array = np.zeros(3)
        slice_location_um_array[MLAPDV_SLICE_TO_INDEX[slice_plane]] = slice_location_um
        slice_voxel = self.bregma_positions_to_atlas_voxels(slice_location_um_array)[slicing_index]

        # Mapping slicing indices to corresponding slice axes
        slice_axes = {
            0: (slice_voxel, slice(None), slice(None)),
            1: (slice(None), slice_voxel, slice(None)),
            2: (slice(None), slice(None), slice_voxel)
        }

        # Slice the annotation based on the selected plane and location
        slc = self.bg_atlas.annotation[slice_axes[slicing_index]]
        if return_full_annotation:
            return slc
        else:
            remapped_slc = np.zeros_like(slc)
            for acronym in self.structures.acronym:
                if acronym == 'root':
                    continue
                area_mask_num = self.get_structure_mask_from_slice(slc,acronym)
                msk = area_mask_num != 0 
                remapped_slc[msk] = area_mask_num[msk]
            return remapped_slc
        
    def get_structure_mask_from_slice(self,slc, structure_acronym):
        """Get a mask of a structure from a 2D slice of the atlas annotation volume. Useful to get the
        mask of a parent region is desired when the parent is not present in the annotation volume (e.g. root, MO, VIS, etc.).
        Similar to bg_atlas.get_structure_mask() but for a 2D slice, and therefore much faster.

        Parameters
        ----------
        slc : ndarray
            a 2D slice of the atlas annotation volume
        structure_acronym : string
            the structure acronym to get the mask for

        Returns
        -------
        ndarray
            the mask of the structure in the slice, same size as slc
        """
        structure_id = self.bg_atlas.structures[structure_acronym]["id"]
        descendants = self.bg_atlas.get_structure_descendants(structure_acronym)
        descendant_ids = [self.bg_atlas.structures[descendant]['id'] for descendant in descendants]
        descendant_ids.append(structure_id)
        mask_slice = np.zeros(slc.shape, slc.dtype)
        mask_slice[np.isin(slc, descendant_ids)] = structure_id
        return mask_slice
        
    ##################################
    #####  Properties ################
    ##################################

    @cached_property
    def remapped_annotation(self):
        '''
        This function computes the remapped annotation volume if a mapping is provided.
        It is quite slow since it remaps the whole volume. It is better to slice up the volume
        first and then remap a slice if you only need to plot a particular 2D slice.
        '''
        # TODO: speed this function up
        print('Computing and caching remapped annotation. This may take some time.')
        res = np.empty_like(self.bg_atlas.annotation)
        for area_acronym in tqdm(self.mapping_structures):
            area_mask_num = self.bg_atlas.get_structure_mask(area_acronym)
            msk = area_mask_num != 0
            res[msk] = area_mask_num[msk]
        return res

    @property
    def atlas_properties(self):
        '''Primarily used to write the atlas properties to a json file'''
        return dict(name=self.name,
                    min_tree_depth=self.min_tree_depth,
                    max_tree_depth=self.max_tree_depth,
                    mapping=self.mapping,
                    visible_regions=self.visible_atlas_regions)
    
    @property
    def visible_atlas_regions(self):
        return list(self.visible_region_actors.keys())
    
    @property
    def all_atlas_regions(self):
        return self.structures.acronym.values

    def __del__(self):
        '''A modified destructor to remove any actors from the PyVista plotter when the object is deleted.'''
        temp = list(self.visible_region_actors.keys())
        for region in temp:
            self.remove_atlas_region_mesh(region)
        if self.show_root:
            self.plotter.remove_actor(self.root_actor)
        if self.show_bregma:
            self.plotter.remove_actor(self.bregma_actor)