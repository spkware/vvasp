from .utils import *
import shutil
import os
from git import Repo

from .default_prefs import (ALL_PREFS, 
                            DEFAULT_PROBE_GEOMETRIES,
                            EXPERIMENT_DIR,
                            MESH_DIR,
                            USER_MESH_DIR,
                            EXPORT_DIR,
                            ALL_PREF_FILES, 
                            PREFS_FILE, 
                            DEFAULT_PREFERENCES, 
                            MOVEMENT_KEYBINDS_FILE, 
                            DEFAULT_MOVEMENT_KEYBINDS, 
                            PROBE_GEOMETRIES_FILE,
                            STATIC_KEYBINDS_FILE,
                            USER_MESH_TRANSFORMATIONS_FILE,
                            USER_MESH_TRANSFORMATIONS,
                            DEFAULT_STATIC_KEYBINDS)

def __fix_json_indent(text):
    import re
    return  re.sub('{"', '{\n"', re.sub('\[\[', '[\n[', re.sub('\]\]', ']\n]', re.sub('}', '\n}', text))))

def __dump_json(filepath, data):
    with open(filepath, 'w') as fd:
        json.dump(data, fd, sort_keys=False, indent=4)

def __merge_with_default_order(current, defaults):
    merged = {}

    # Keep canonical default key order first.
    for key, default_value in defaults.items():
        merged[key] = current.get(key, default_value)

    # Preserve any user-defined keys after defaults.
    for key, value in current.items():
        if key not in merged:
            merged[key] = value

    return merged

def __setup_prefs():
    if not EXPERIMENT_DIR.exists():
        print(f'Creating experiment directory at {EXPERIMENT_DIR}')
        EXPERIMENT_DIR.mkdir(parents=True)

    if not EXPORT_DIR.exists():
        print(f'Creating export directory at {EXPORT_DIR}')
        EXPORT_DIR.mkdir()
    
    if not MESH_DIR.exists():
        print(f'Creating mesh directory at {MESH_DIR}')
        MESH_DIR.mkdir()
    
    if not USER_MESH_DIR.exists():
        print(f'Creating user mesh directory at {USER_MESH_DIR}')
        USER_MESH_DIR.mkdir()
        sourcepath = Path(__file__).resolve().parents[1] / 'meshes' / 'logo.stl'
        destpath = Path(USER_MESH_DIR) / 'logo.stl'
        print(sourcepath, destpath)
        shutil.copy(sourcepath, destpath)

    if not PREFS_FILE.parent.exists():
        PREFS_FILE.parent.mkdir()

    for fpath, prefs in zip(ALL_PREF_FILES, ALL_PREFS):
        __dump_json(fpath, prefs)
        print(f'Preferences file created at {fpath}')

def __load_prefs():
    with open(PREFS_FILE,'r') as fd:
        prefs = json.load(fd)
    prefs = __merge_with_default_order(prefs, DEFAULT_PREFERENCES)

    with open(MOVEMENT_KEYBINDS_FILE,'r') as fd:
        movement_keybinds = json.load(fd)
    movement_keybinds = __merge_with_default_order(movement_keybinds, DEFAULT_MOVEMENT_KEYBINDS)

    with open(STATIC_KEYBINDS_FILE,'r') as fd:
        static_keybinds = json.load(fd)
    static_keybinds = __merge_with_default_order(static_keybinds, DEFAULT_STATIC_KEYBINDS)

    with open(PROBE_GEOMETRIES_FILE,'r') as fd:
        probe_geometries = json.load(fd)
    probe_geometries = __merge_with_default_order(probe_geometries, DEFAULT_PROBE_GEOMETRIES)
    if USER_MESH_TRANSFORMATIONS_FILE.exists():
        with open(USER_MESH_TRANSFORMATIONS_FILE,'r') as fd:
            custom_user_mesh_transformations = json.load(fd)
    else:
        custom_user_mesh_transformations = USER_MESH_TRANSFORMATIONS

    return prefs, movement_keybinds, static_keybinds, probe_geometries, custom_user_mesh_transformations

def list_experiments():
    raise NotImplementedError
    return experiments_list

def update_prefs():
    raise NotImplementedError

def save_experiment(probes, atlas, filepath):
    repo = Repo(Path(__file__).resolve().parents[1])
    git_commit_hash = repo.head.commit.hexsha[:7]

    experiment_data = dict(probes = [probe.probe_properties for probe in probes],
                           atlas = atlas.atlas_properties,
                           vvasp_commit_version = git_commit_hash,)
    print(f'Saving to {filepath}', flush=True)
    with open(Path(filepath),'w') as fd:
        json.dump(experiment_data, fd, sort_keys=False, indent=4)


def load_experiment_file(filepath):
    filepath = Path(filepath).with_suffix('.json')
    if not os.path.exists(filepath):
        return None
    with open(str(filepath),'r') as fd:
        experiment_data = json.load(fd)
    return experiment_data

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


if not PREFS_FILE.exists():
    __setup_prefs()

preferences, movement_keybinds, static_keybinds, probe_geometries, custom_user_mesh_transformations = __load_prefs()
