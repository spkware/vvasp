from pathlib import Path
import pyvista as pv
import json

PREFS_FILE = Path('~').expanduser() / '.vvasp' / 'preferences.json'
EXPERIMENT_DIR = Path('~').expanduser() / 'vvasp_experiments'
ATLAS_DIR = Path('~').expanduser()/'.brainglobe'

DEFAULT_PREFERENCES = {'atlas':'allen_mouse_25um_v1.2',
                        'bregma_locations':{'allen_mouse_25um_v1.2':[216, 18,228],
                                            },
                       'warn_collisions':True,
                       'warn_overwrite':True,
                       'warn_delete':True,}

if not EXPERIMENT_DIR.exists():
    EXPERIMENT_DIR.mkdir()

if not PREFS_FILE.parent.exists():
    PREFS_FILE.parent.mkdir()

def __setup_prefs():
    with open(PREFS_FILE,'w') as fd:
        json.dump(DEFAULT_PREFERENCES,
                  fd,
                  sort_keys=True,
                  indent=4)
    print(f'Preferences file created at {PREFS_FILE}')

def __load_prefs():
    with open(PREFS_FILE,'r') as fd:
        prefs = json.load(fd)
    for k in DEFAULT_PREFERENCES:
        if k not in prefs.keys():
            prefs[k] = DEFAULT_PREFERENCES[k]
    return prefs

def list_experiments():
    raise NotImplementedError
    return experiments_list

def update_prefs():
    raise NotImplementedError

def save_experiment():
    raise NotImplementedError

def save_experiment_as():
    raise NotImplementedError

def load_experiment():
    raise NotImplementedError

if not PREFS_FILE.exists():
    __setup_prefs()

def load_structure_mesh(atlaspath,structures,acronym):
    # meshes are in um
    id = structures[structures.acronym == acronym].id.values
    if len(id):
        id = id[0]
    else:
        return
    mesh = atlaspath/'meshes'/f'{id}.obj'
    mesh = pv.read(mesh)
    return mesh, structures[structures.acronym == acronym].iloc[0]


preferences = __load_prefs()