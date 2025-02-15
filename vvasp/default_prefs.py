
from .utils import Path, get_blackrock_array_geometry

PREFS_FILE = Path().home() / 'vvasp' / 'preferences.json'
PROBE_GEOMETRIES_FILE = Path().home() / 'vvasp' / 'probe_geometries.json'
MOVEMENT_KEYBINDS_FILE = Path().home() / 'vvasp' / 'movement_keybinds.json'
STATIC_KEYBINDS_FILE = Path().home() / 'vvasp' / 'static_keybinds.json'
EXPERIMENT_DIR = Path().home() / 'vvasp' / 'experiments'
MESH_DIR = Path(__file__).resolve().parents[1] / 'meshes'
EXPORT_DIR = Path().home() / 'vvasp' / 'exports'
USER_MESH_DIR = Path().home() / 'vvasp' / 'custom_user_meshes'
USER_MESH_TRANSFORMATIONS_FILE = Path().home() / 'vvasp' / 'custom_user_mesh_transformations.json'
ATLAS_DIR = Path().home() /'.brainglobe'


ALL_PREF_FILES = [PREFS_FILE, MOVEMENT_KEYBINDS_FILE, STATIC_KEYBINDS_FILE, PROBE_GEOMETRIES_FILE, USER_MESH_TRANSFORMATIONS_FILE]


DEFAULT_PREFERENCES = {'default_atlas':'allen_mouse_25um',
                       'atlas_transformations':
                               {'allen_mouse_25um':
                                       {'bregma_location':[216, 18,228],
                                        'angles':[90, -5, 90]}, # -5 corrects for small tilt in the atlas
                                'whs_sd_rat_39um':
                                        {'bregma_location':[371, 72, 266],
                                         'angles':[90, -4, 90]}, # -4 corrects for a small tilt in the atlas
                               },
                       'default_save_dir':str(EXPERIMENT_DIR),
                       'user_mesh_dir':str(USER_MESH_DIR),
                       'export_dir':str(EXPORT_DIR),
                       'atlas_dir':str(ATLAS_DIR), # the location of brainglobe atlas files
                       'warn_collisions':True,
                       'warn_overwrite':True,
                       'warn_delete':True,}

USER_MESH_TRANSFORMATIONS = {'logo':{'angles':[0, 0, 0],
                                     'origin':[0, 0, 0],
                                     'scale':1000}}

DEFAULT_MOVEMENT_KEYBINDS = {'a': ['left', 100],
                             'd': ['right', 100],
                             'f': ['dorsal', 100],
                             'c': ['ventral', 100],
                             'w': ['anterior', 100],
                             's': ['posterior', 100],
                             'h': ['home', 0],
         
                             'Ctrl+a': ['left', 10],
                             'Ctrl+d': ['right', 10],
                             'Ctrl+f': ['dorsal', 10],
                             'Ctrl+c': ['ventral', 10],
                             'Ctrl+w': ['anterior', 10],
                             'Ctrl+s': ['posterior', 10],
         
                             'Shift+a': ['rotate left', 5],
                             'Shift+d': ['rotate right', 5],
                             'Shift+w': ['tilt down', 5],
                             'Shift+s': ['tilt up', 5],

                             'Ctrl+Shift+a': ['rotate left', 1],
                             'Ctrl+Shift+d': ['rotate right', 1],
                             'Ctrl+Shift+w': ['tilt down', 1],
                             'Ctrl+Shift+s': ['tilt up', 1],
                             
                             'q': ['spin left', 5],
                             'e': ['spin right', 5],

                             'Ctrl+q': ['spin left', 1],
                             'Ctrl+e': ['spin right', 1],
         
                             'Shift+f': ['retract', 100],
                             'Shift+c': ['advance', 100],
                             'Ctrl+Shift+f': ['retract', 10],
                             'Ctrl+Shift+c': ['advance', 10],}

DEFAULT_STATIC_KEYBINDS = {'Ctrl+o': 'open_experiment',
                           #'Ctrl+s': 'save',
                           #'Ctrl+Shift+s': 'save as',
                           #'Ctrl+Shift+o': 'open',
                           #'Ctrl+e': 'export',
                           #'Ctrl+Shift+e': 'export as',
                           'n': 'next_object',
                           'p': 'previous_object',
                           'Del': 'delete_object',}

__utah10x10coords, __utah10x10dims = get_blackrock_array_geometry(10, 10, pitch_um=400, shank_dims=[30, -1000, 0])

DEFAULT_PROBE_GEOMETRIES = {'NP1': {'full_name': 'Neuropixels 1.0',
                                    'shank_offsets_um': [[-35, 0, 0]], # the offsets from the probe origin
                                    'shank_dims_um': [[70, 10000, 0]]}, # dimensions of the shank in um [x, y, z]
                            'NP24': {'full_name': 'Neuropixels 2.0 - 4Shank',
                                     'shank_offsets_um': [[-410, 0, 0], 
                                                          [-160, 0, 0],
                                                          [90, 0, 0],
                                                          [340, 0, 0]], 
                                     'shank_dims_um': [[70, 10000, 0],
                                                       [70, 10000, 0],
                                                       [70, 10000, 0],
                                                       [70, 10000, 0]]},
                            'utah10x10': {'full_name': 'Utah Array 1043-29 (10 x 10)',
                                     'shank_offsets_um': __utah10x10coords,
                                     'shank_dims_um': __utah10x10dims},}

ALL_PREFS = [DEFAULT_PREFERENCES, DEFAULT_MOVEMENT_KEYBINDS, DEFAULT_STATIC_KEYBINDS, DEFAULT_PROBE_GEOMETRIES, USER_MESH_TRANSFORMATIONS]