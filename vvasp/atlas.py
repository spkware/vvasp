"""
A module for working with brain atlases in VVASP, extending BrainGlobeAtlas functionality.

This module provides tools for:
- Loading and managing brain atlas data
- Transforming between bregma and atlas coordinate spaces
- Visualizing 2D and 3D atlas regions
- Mapping brain regions and their hierarchies
"""

import matplotlib.pyplot as plt
from tqdm import tqdm
from functools import cached_property
from brainglobe_atlasapi import BrainGlobeAtlas

from . import io
from .utils import *

def list_availible_atlases():
    """
    List all available atlases in the atlas directory.

    Returns
    -------
    list
        List of atlas names as strings.
    """
    return [x.name for x in io.ATLAS_DIR.glob('*')]

SLICE_TO_BG_SPACE = dict(coronal='frontal',
                         sagittal='sagittal',
                         transverse='horizontal')

MLAPDV_SLICE_TO_INDEX = dict(sagittal=0, coronal=1, transverse=2)

PV_KWARG_DEFAULTS = dict(opacity=.7,
                         render=False,
                         silhouette=False) 

class VVASPAtlas(BrainGlobeAtlas):
    """
    Extended BrainGlobeAtlas with additional functionality for visualization and coordinate transforms.

    This class extends BrainGlobeAtlas to provide:
    1. Region hierarchy mapping and parent-child relationships
    2. Coordinate transformations between bregma and atlas spaces
    3. Probe trajectory computation through atlas space
    4. 3D visualization using PyVista
    5. 2D slice visualization of atlas annotations

    Parameters
    ----------
    vistaplotter : pyvista.Plotter, optional
        PyVista plotter instance for 3D visualization
    atlas_name : str, optional
        Name of the atlas to load
    show_root : bool, default=True
        Whether to show the root mesh
    show_bregma : bool, default=True
        Whether to show bregma point
    mapping : str, default='Beryl'
        Name of region mapping to use
    min_tree_depth : int, optional
        Minimum depth in region hierarchy to include
    max_tree_depth : int, optional
        Maximum depth in region hierarchy to include
    transform_to_stereotaxic_space : bool, default=True
        Whether to transform coordinates to stereotaxic space
    check_latest_atlas : bool, default=False
        Whether to check for latest atlas version
    bregma_location : array-like, optional
        Custom bregma location in atlas space
    rotation_angles : array-like, optional
        Custom rotation angles for coordinate transform
    scaling : array-like, optional
        Custom scaling factors for coordinate transform
    """
    def __init__(self, 
                 vistaplotter=None,
                 atlas_name=None,
                 show_root=True,
                 show_bregma=True,
                 mapping='Beryl',
                 min_tree_depth=None,
                 max_tree_depth=None,
                 transform_to_stereotaxic_space=True,
                 check_latest_atlas=False,
                 bregma_location=None,
                 rotation_angles=None,
                 scaling=None):
        atlas_name = atlas_name or io.preferences['default_atlas']
        super().__init__(atlas_name=atlas_name, check_latest=check_latest_atlas)

        self.name = atlas_name
        self.plotter = vistaplotter
        self.transformed = transform_to_stereotaxic_space
        self.min_tree_depth = min_tree_depth
        self.max_tree_depth = max_tree_depth
        self.mapping = mapping
        self.meshes = {}
        self.visible_region_actors = {}
        self.show_root = show_root
        self.show_bregma = show_bregma
        self.structures_list = pd.DataFrame(self.structures_list) # make BrainGlobeAtlas attribute a dataframe for easier indexing
        self.structures_list['mesh_is_loaded'] = False # track which meshes we want to load
        self._select_region_meshes_to_load(mapping, min_tree_depth, max_tree_depth)
        self._initialize_transformations(bregma_location=bregma_location, rotation_angles=rotation_angles, scaling=scaling)
        if vistaplotter is not None:
            self._load_meshes()
            self._show_root_and_bregma_actors()
        
    @classmethod
    def load_atlas_from_experiment_file(cls, experiment_file_path, vistaplotter=None):
        """
        Create a VVASPAtlas instance from a VVASP experiment file.

        Parameters
        ----------
        experiment_file_path : str or Path
            Path to the experiment file
        vistaplotter : pyvista.Plotter, optional
            PyVista plotter instance for 3D visualization

        Returns
        -------
        VVASPAtlas
            New atlas instance configured according to experiment file
        """
        atlas_data = io.load_experiment_file(experiment_file_path)['atlas']

        # Format the dictionary to pass the whole thing
        atlas_data['atlas_name'] = atlas_data.pop('name')
        visible_regions = atlas_data.pop('visible_regions')

        # Ensure compatibility with legacy files
        atlas_data.setdefault('min_tree_depth', None)
        atlas_data.setdefault('max_tree_depth', None)
        atlas_data.setdefault('mapping', None)

        # return instance of the class
        new_atlas = cls(vistaplotter, **atlas_data)
        for region in visible_regions:
            new_atlas.add_atlas_region_mesh(region)
        return new_atlas


    def _select_region_meshes_to_load(self, mapping='Beryl', min_tree_depth=None, max_tree_depth=None):
        """
        Select which region meshes should be loaded based on mapping or tree depth criteria.

        Parameters
        ----------
        mapping : str, optional
            Name of region mapping file to use
        min_tree_depth : int, optional
            Minimum depth in region hierarchy to include
        max_tree_depth : int, optional
            Maximum depth in region hierarchy to include

        Raises
        ------
        ValueError
            If both mapping and tree depth parameters are provided
        """
        if mapping is not None and min_tree_depth is None and max_tree_depth is None:
            mapping_file = Path(__file__).parent.parent / 'assets' / f'{mapping}.csv'
            mapping_structures = pd.read_csv(mapping_file)['acronym'].values
            self.mapping_structures = mapping_structures
            mesh_inds_to_show = self.structures_list.acronym.isin(mapping_structures)
        elif min_tree_depth is not None and max_tree_depth is not None and mapping is None:
            # get the inds within the desired tree depths
            mesh_inds_to_show = self.structures_list[self.structures_list['structure_id_path'].apply(lambda x: min_tree_depth <= len(x) <= max_tree_depth)].index
            temp = np.zeros(len(self.structures_list)).astype(bool)
            temp[mesh_inds_to_show] = 1
            mesh_inds_to_show = temp
        else:
            raise ValueError('Specify either min_tree_depth/max_tree_depth or mapping, not both.')

        self.structures_list['mesh_is_loaded'] = mesh_inds_to_show 
        self.structures_list.loc[self.structures_list.acronym == 'root','mesh_is_loaded'] = 1 # always load the root mesh

    def _initialize_transformations(self, bregma_location=None, rotation_angles=None, scaling=None):
        """
        Initialize coordinate transformation parameters.

        Parameters
        ----------
        bregma_location : array-like, optional
            Custom bregma location in atlas space
        rotation_angles : array-like, optional
            Custom rotation angles for coordinate transform
        scaling : array-like, optional
            Custom scaling factors for coordinate transform
        """
        prefs = io.preferences['atlas_transformations'][self.name]
        self.bregma_location = np.array(bregma_location) if bregma_location is not None else np.array(prefs['bregma_location'])
        self.bregma_location_scaled = self.bregma_location * self.metadata['resolution']
        self.rotation_angles = np.array(rotation_angles) if rotation_angles is not None else np.array(prefs['angles'])
        self.rotation_matrix = rotation_matrix_from_degrees(*self.rotation_angles, order='xyz')
        self.scaling = np.array(scaling) if scaling is not None else np.array(prefs.get('scaling',[1.,1.,1.])) # no scaling if it doesn't exist

    def _load_meshes(self):
        """
        Load region meshes and apply appropriate transformations.
        
        Loads meshes for all selected regions, applies rotation, translation,
        and scaling according to the atlas configuration.
        """
        for region_acronym in self.structures_list_remapped.acronym:
            try:
                mesh = pv.read(self.meshfile_from_structure(region_acronym))
            except FileNotFoundError:
                print(f'Mesh file could not be found for {region_acronym}')
                continue
            if self.transformed:
                mesh.translate(-self.bregma_location_scaled, inplace=True)
                mesh.points = np.dot(mesh.points, self.rotation_matrix.T)
                mesh.scale(self.scaling, inplace=True)
            self.meshes[region_acronym] = mesh
    
    def _show_root_and_bregma_actors(self):
        """
        Add root mesh and bregma point actors to the PyVista plotter if enabled.
        """
        # Handle showing root and bregma meshes
        if self.show_root and self.plotter is not None:
            self.root_actor = self.plotter.add_mesh(self.meshes['root'],
                                  color=self.meshcolor('root'),
                                  opacity=0.08,
                                  silhouette=False,
                                  name='root')
        if self.show_bregma and self.plotter is not None:
            self.bregma_actor = self.plotter.add_mesh(io.pv.Sphere(radius=100, center=(0, 0, 0)))

    @property
    def structures_list_remapped(self):
        return self.structures_list[self.structures_list.mesh_is_loaded == 1] 
    
    def meshcolor(self, acronym):
        """
        Get the RGB color for a given region acronym.

        Parameters
        ----------
        acronym : str
            Region acronym

        Returns
        -------
        tuple
            RGB color triplet
        """
        return self.structures[acronym]['rgb_triplet']       

    def bregma_positions_to_structures(self, positions_um, hierarchy_lev=None):
        """
        Convert positions in bregma space to structure acronyms.

        Parameters
        ----------
        positions_um : array-like
            Positions in micrometers relative to bregma
        hierarchy_lev : int, optional
            Hierarchy level to use for structure lookup

        Returns
        -------
        list
            List of structure acronyms corresponding to each position
        """
        voxels = self.bregma_positions_to_atlas_voxels(positions_um)
        region_acronyms = [self.structure_from_coords(a, as_acronym=True, hierarchy_lev=hierarchy_lev) for a in voxels]
        return region_acronyms

    def bregma_positions_to_atlas_voxels(self, mlapdv_positions_um, round=True):
        """
        Convert positions from bregma space to atlas voxel coordinates.

        Parameters
        ----------
        mlapdv_positions_um : array-like
            Positions in micrometers relative to bregma (ML, AP, DV)
        round : bool, default=True
            Whether to round the voxel coordinates to integers

        Returns
        -------
        ndarray
            Positions in atlas voxel coordinates
        """
        mlapdv_positions_um = mlapdv_positions_um / self.scaling
        mlapdv_positions_um = np.dot(mlapdv_positions_um, self.rotation_matrix)
        mlapdv_positions_um = mlapdv_positions_um + self.bregma_location_scaled
        voxels = mlapdv_positions_um / self.metadata['resolution']
        # TODO: handle case where outside of volume and either clip (with warning) or raise error?
        if round:
            return np.round(voxels).astype(int)
        else:
            return voxels
    
    def atlas_voxels_to_bregma_positions(self, voxels):
        """
        Convert positions from atlas voxel coordinates to bregma space.

        Parameters
        ----------
        voxels : array-like
            Positions in atlas voxel coordinates

        Returns
        -------
        ndarray
            Positions in micrometers relative to bregma (ML, AP, DV)
        """
        positions_um = np.array(voxels) * self.metadata['resolution']
        positions_um = positions_um - self.bregma_location_scaled
        positions_um = np.dot(positions_um, self.rotation_matrix.T)
        positions_um = positions_um * self.scaling
        return positions_um

    def atlas_voxels_to_annotation_boundaries(self, bresenham_line, return_midpoints=False):
        """
        Find region boundaries along a line through the atlas volume.

        Parameters
        ----------
        bresenham_line : array-like
            Line of voxel coordinates through the atlas volume
        return_midpoints : bool, default=False
            Whether to return midpoints between region boundaries

        Returns
        -------
        ndarray
            Coordinates of region boundaries
        ndarray, optional
            Coordinates of midpoints between boundaries (if return_midpoints=True)
        """
        bresenham_line = np.clip(bresenham_line, 0, np.array(self.annotation.shape) - 1)
        region_ids = self.annotation[tuple(bresenham_line.T)]
        region_boundaries = bresenham_line[np.where(np.diff(region_ids) != 0)]
        region_boundaries = np.vstack([bresenham_line[0], region_boundaries, bresenham_line[-1]])
        if not return_midpoints:
            return region_boundaries
        else:
            if region_boundaries.shape[0] == 0:
                midpoints = np.empty((0,3))
            else:
                midpoints = ((region_boundaries[:-1] + region_boundaries[1:]) / 2).astype(int)
            return region_boundaries, midpoints

    def show_all_regions(self, side='both', add_root=False, **pv_kwargs):
        """
        Show all selected regions in the 3D visualization.

        Parameters
        ----------
        side : {'both', 'left', 'right'}, default='both'
            Which side(s) of the brain to show
        add_root : bool, default=False
            Whether to include the root region
        **pv_kwargs
            Additional keyword arguments passed to PyVista's add_mesh
        """
        for region in self.structures_list_remapped.acronym:
            if region != 'root' or add_root:
                self.add_atlas_region_mesh(region, side=side, **pv_kwargs)

    def add_atlas_region_mesh(self, region_acronym, side='both', force_replot=False, **pv_kwargs):
        """
        Add a specific region to the 3D visualization.

        Parameters
        ----------
        region_acronym : str
            Acronym of the region to add
        side : {'both', 'left', 'right'}, default='both'
            Which side(s) of the brain to show
        force_replot : bool, default=False
            Whether to replot the region even if already visible
        **pv_kwargs
            Additional keyword arguments passed to PyVista's add_mesh

        Raises
        ------
        ValueError
            If no PyVista plotter is available or if side is invalid
        """
        if self.plotter is None:
            raise ValueError('No PyVista plotter found. Instantiate the VVASPAtlas with a PyVista plotter to render meshes.')
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
                              color=self.meshcolor(region_acronym),
                              **pv_kwargs)
        self.visible_region_actors.update({region_acronym: actor})
    
    def remove_atlas_region_mesh(self, region_acronym):
        """
        Remove a specific region from the 3D visualization.

        Parameters
        ----------
        region_acronym : str
            Acronym of the region to remove
        """
        if actor := self.visible_region_actors.pop(region_acronym, None):
            self.plotter.remove_actor(actor)
        else:
            print(f'No region {region_acronym} to remove')
    
    def clear_atlas(self):
        """
        Remove all regions from the 3D visualization.
        """
        for region in self.visible_region_actors:
            self.remove_atlas_region_mesh(region)
        self.visible_region_actors = {}
    
    ##################################
    ##### 2D slicing and plotting functions ######
    ##################################

    def plot_2d_slice(self, slice_plane, slice_location_um, ax=None):
        """
        Plot a 2D slice from the atlas annotation volume.

        Parameters
        ----------
        slice_plane : {'coronal', 'sagittal', 'transverse'}
            Plane to slice along
        slice_location_um : float
            Location of slice in micrometers relative to bregma
        ax : matplotlib.axes.Axes, optional
            Axes to plot on, creates new figure if None

        Returns
        -------
        tuple
            (matplotlib.figure.Figure, matplotlib.axes.Axes)
        """        
        if ax is None:
            fig, ax = plt.subplots()
        slc = self.get_2d_slice(slice_plane, slice_location_um)
        colored_slice = np.ones((slc.shape[0], slc.shape[1], 3)).astype(int) * 255 # make background white
        unique_ids = np.unique(slc)
        unique_ids = unique_ids[unique_ids != 0] # need to drop the 0 value (background)
        for id in unique_ids:
            color = self.structures[id]['rgb_triplet']
            colored_slice[slc == id] = color
        ax.imshow(colored_slice)
        return fig, ax
    
    def get_2d_slice(self, slice_plane, slice_location_um, return_full_annotation=False):
        """
        Get a 2D slice from the atlas annotation volume.

        Parameters
        ----------
        slice_plane : {'coronal', 'sagittal', 'transverse'}
            Plane to slice along
        slice_location_um : float
            Location of slice in micrometers relative to bregma
        return_full_annotation : bool, default=False
            Whether to return full annotation or remapped version

        Returns
        -------
        ndarray
            2D array of region IDs at the specified slice

        Raises
        ------
        AssertionError
            If slice_plane is invalid
        """
        assert slice_plane in SLICE_TO_BG_SPACE.keys(), f"Invalid slice plane, must be one of {SLICE_TO_BG_SPACE.keys()}"

        # use brainglobe space definition to ensure consistency across atlases, this finds the proper axis to slice along
        slicing_index = self.space.sections.index(SLICE_TO_BG_SPACE[slice_plane]) 

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
        slc = self.annotation[slice_axes[slicing_index]]
        if return_full_annotation:
            return slc
        else:
            remapped_slc = np.zeros_like(slc)
            for acronym in self.structures_list_remapped.acronym:
                #if acronym == 'root':
                #    continue
                area_mask_num = self.get_structure_mask_from_slice(slc,acronym)
                msk = area_mask_num != 0 
                remapped_slc[msk] = area_mask_num[msk]
            return remapped_slc
        
    def get_structure_mask_from_slice(self, slc, structure_acronym):
        """
        Get a mask of a structure from a 2D slice.

        Parameters
        ----------
        slc : ndarray
            2D slice from atlas annotation volume
        structure_acronym : str
            Acronym of structure to mask

        Returns
        -------
        ndarray
            Binary mask of the structure in the slice
        """
        structure_id = self.structures[structure_acronym]["id"]
        descendants = self.get_structure_descendants(structure_acronym)
        descendant_ids = [self.structures[descendant]['id'] for descendant in descendants]
        descendant_ids.append(structure_id)
        mask_slice = np.zeros(slc.shape, slc.dtype)
        mask_slice[np.isin(slc, descendant_ids)] = structure_id
        return mask_slice
        
    ##################################
    #####  Properties ################
    ##################################

    @cached_property
    def remapped_annotation(self):
        """
        Get remapped version of full annotation volume.

        Returns
        -------
        ndarray
            Full annotation volume with regions remapped according to current mapping

        Notes
        -----
        This is a computationally expensive operation that is cached after first call.
        """
        print('Computing and caching remapped annotation. This may take some time.')
        res = np.empty_like(self.annotation)
        for area_acronym in tqdm(self.mapping_structures):
            area_mask_num = self.get_structure_mask(area_acronym)
            msk = area_mask_num != 0
            res[msk] = area_mask_num[msk]
        return res

    @property
    def atlas_properties(self):
        """
        Get dictionary of atlas properties for serialization.

        Returns
        -------
        dict
            Dictionary containing atlas configuration parameters
        """
        return dict(name=self.name,
                    min_tree_depth=self.min_tree_depth,
                    max_tree_depth=self.max_tree_depth,
                    mapping=self.mapping,
                    visible_regions=self.visible_atlas_regions,
                    bregma_location=self.bregma_location.tolist(),
                    rotation_angles=self.rotation_angles.tolist(),
                    scaling=self.scaling.tolist())
    
    @property
    def visible_atlas_regions(self):
        """
        Get list of currently visible regions.

        Returns
        -------
        list
            List of region acronyms currently shown in visualization
        """
        return list(self.visible_region_actors.keys())
    
    @property
    def all_atlas_regions(self):
        """
        Get list of all available regions.

        Returns
        -------
        list
            List of all region acronyms in the atlas
        """
        return self.structures.acronym.values

    def __del__(self):
        """
        Clean up PyVista actors when object is deleted.
        """
        temp = list(self.visible_region_actors.keys())
        for region in temp:
            self.remove_atlas_region_mesh(region)
        if self.show_root and self.plotter is not None:
            self.plotter.remove_actor(self.root_actor)
        if self.show_bregma and self.plotter is not None:
            self.plotter.remove_actor(self.bregma_actor)