"""ZenExport v5 - Fusion 360 Script for Local Design Backup.

This script automates exporting Fusion 360 designs locally with:
- Auto-Versioning: Saves numbered history (v01, v02) for CAD files
- Thumbnails: Generates viewport preview image
- Auto-Open: Launches folder after export
- JSON Persistence: Remembers session project path
- Robust Logging: Detailed console output

Workflow:
    - Load Config / Detect Mode
    - Generate Next Version number for CAD files
    - Capture Thumbnail
    - Synchronized Export (CAD+STL)
    - Open Windows Explorer

Author: ZenExport (Generated via GEMINI.md)
Version: 5.0
"""

import adsk.core
import adsk.fusion
import traceback
import os
import json
import re
import glob

# ============================================================================
# CONSTANTS
# ============================================================================

MESH_REFINEMENT = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
CONFIG_FILENAME = "session_config.json"
SESSION_ATTR_GROUP = "ZenExport"


# ============================================================================
# LOGGING HELPER
# ============================================================================

def log_to_console(app: adsk.core.Application, message: str) -> None:
    """Logs a message to the Text Commands palette."""
    text_palette = app.userInterface.palettes.itemById("TextCommands")
    if text_palette:
        text_palette.writeText(f"[ZenExport] {message}")


# ============================================================================
# SESSION PERSISTENCE (JSON)
# ============================================================================

def get_config_path() -> str:
    script_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(script_dir, CONFIG_FILENAME)

def load_config() -> dict | None:
    path = get_config_path()
    if not os.path.exists(path): return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def save_config(project_name: str, export_dir: str) -> None:
    path = get_config_path()
    data = {"current_project_name": project_name, "last_save_directory": export_dir}
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except:
        pass


# ============================================================================
# UTILS & VERSIONING
# ============================================================================

def sanitize_filename(name: str) -> str:
    invalid = '<>:"/\\|?*'
    for char in invalid:
        name = name.replace(char, "_")
    return name

def is_shift_held() -> bool:
    try:
        import ctypes
        return bool(ctypes.windll.user32.GetAsyncKeyState(VK_SHIFT) & 0x8000)
    except:
        # Define constant if not imported
        return False
        
# Re-define VK_SHIFT locally just in case
VK_SHIFT = 0x10

def ensure_folder_exists(app: adsk.core.Application, folder_path: str) -> None:
    if os.path.exists(folder_path):
        log_to_console(app, f"Targeting existing directory: {folder_path}")
    else:
        log_to_console(app, f"Creating new directory: {folder_path}")
        os.makedirs(folder_path, exist_ok=True)

def get_next_version_number(cad_folder: str) -> int:
    """Finds the next available version number based on vXX subfolders.
    
    Looks for folders: /CAD/v01/, /CAD/v02/
    Returns: Next integer (e.g. 2)
    """
    if not os.path.exists(cad_folder):
        return 1
        
    items = os.listdir(cad_folder)
    versions = []
    regex = re.compile(r'^v(\d+)$')
    
    for item in items:
        if os.path.isdir(os.path.join(cad_folder, item)):
            match = regex.match(item)
            if match:
                versions.append(int(match.group(1)))
            
    if not versions:
        return 1
        
    return max(versions) + 1


# ============================================================================
# EXPORT LOGIC
# ============================================================================

def save_thumbnail(app: adsk.core.Application, folder: str, project_name: str) -> bool:
    """Captures and saves a viewport snapshot."""
    try:
        viewport = app.activeViewport
        fname = "_preview.png" # Fixed name for root preview
        path = os.path.join(folder, fname)
        
        # Save 400x400 transparent PNG
        viewport.saveAsImageFile(path, 400, 400)
        log_to_console(app, f"Thumbnail saved: {fname}")
        return True
    except Exception as e:
        log_to_console(app, f"Thumbnail failed: {e}")
        return False

def export_cad_files(
    app: adsk.core.Application,
    design: adsk.fusion.Design,
    cad_folder: str,
    versioned_name: str
) -> tuple[bool, bool]:
    """Exports .f3d and .step using the VERSIONED name."""
    export_mgr = design.exportManager
    
    # 1. F3D
    f3d_path = os.path.join(cad_folder, f"{versioned_name}.f3d")
    log_to_console(app, f"Exporting F3D -> {f3d_path}")
    f3d_ok = False
    try:
        opts = export_mgr.createFusionArchiveExportOptions(f3d_path)
        f3d_ok = export_mgr.execute(opts)
    except Exception as e:
        log_to_console(app, f"Error exporting F3D: {e}")

    # 2. STEP
    step_path = os.path.join(cad_folder, f"{versioned_name}.step")
    log_to_console(app, f"Exporting STEP -> {step_path}")
    step_ok = False
    try:
        opts = export_mgr.createSTEPExportOptions(step_path)
        step_ok = export_mgr.execute(opts)
    except Exception as e:
        log_to_console(app, f"Error exporting STEP: {e}")

    return f3d_ok, step_ok

def export_stl_files(
    app: adsk.core.Application,
    design: adsk.fusion.Design,
    bodies: list,
    models_folder: str
) -> tuple[int, int]:
    """Exports individual STLs (Always Overwrite / Latest)."""
    export_mgr = design.exportManager
    success = 0
    fail = 0
    
    for comp_name, body in bodies:
        fname = sanitize_filename(f"{comp_name}_{body.name}.stl")
        dest_path = os.path.join(models_folder, fname)
        
        try:
            opts = export_mgr.createSTLExportOptions(body, dest_path)
            opts.meshRefinement = MESH_REFINEMENT
            if export_mgr.execute(opts):
                success += 1
            else:
                fail += 1
        except Exception as e:
            fail += 1
            log_to_console(app, f"STL Error {fname}: {e}")

    return success, fail

def collect_bodies(design: adsk.fusion.Design) -> list:
    bodies = []
    def traverse(comp, prefix=""):
        name = prefix + comp.name if prefix else comp.name
        for b in comp.bRepBodies:
            if b.isVisible:
                bodies.append((name, b))
        for occ in comp.occurrences:
            if occ.isVisible:
                traverse(occ.component, f"{name}_" if name else "")
    traverse(design.rootComponent)
    return bodies

def perform_sync_export(
    app: adsk.core.Application,
    design: adsk.fusion.Design,
    project_folder: str,
    project_name: str
) -> dict:
    
    # 1. Folders
    cad_folder = os.path.join(project_folder, "CAD")
    models_folder = os.path.join(project_folder, "Models")
    ensure_folder_exists(app, cad_folder)
    ensure_folder_exists(app, models_folder)

    # 2. Thumbnail
    save_thumbnail(app, project_folder, project_name)

    # 3. Versioning (CAD Files Only - Subfolder Strategy)
    ver_num = get_next_version_number(cad_folder)
    version_label = f"v{ver_num:02d}"
    versioned_name = f"{project_name}_{version_label}"
    
    # Create specific version subfolder: /CAD/v01/
    target_cad_folder = os.path.join(cad_folder, version_label)
    ensure_folder_exists(app, target_cad_folder)
    
    log_to_console(app, f"Version Calculated: {versioned_name} -> {target_cad_folder}")

    # 4. Export (CAD to subfolder, STL to /Models)
    f3d, step = export_cad_files(app, design, target_cad_folder, versioned_name)
    
    bodies = collect_bodies(design)
    stl_s, stl_f = 0, 0
    if bodies:
        stl_s, stl_f = export_stl_files(app, design, bodies, models_folder)

    return {
        'f3d': f3d, 'step': step, 
        'stl_ok': stl_s, 'stl_fail': stl_f,
        'version': versioned_name
    }


# ============================================================================
# MAIN
# ============================================================================

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        # 1. Design Info
        try:
            design = adsk.fusion.Design.cast(app.activeProduct)
            if not design: raise ValueError("No active design")
            design_name = sanitize_filename(app.activeDocument.name.split(" v")[0])
        except Exception as e:
            ui.messageBox(f"Error: {e}")
            return

        # 2. Config & Mode
        config = load_config()
        shift = is_shift_held()
        mode = "INIT"
        project_folder = ""
        project_name = ""

        if shift:
            log_to_console(app, "Shift detected: Init Mode")
        elif config and os.path.exists(config.get("last_save_directory", "")):
            project_folder = config["last_save_directory"]
            project_name = config.get("current_project_name", design_name)
            mode = "UPDATE"
            log_to_console(app, f"Config loaded: Update Mode ({project_folder})")

        # 3. Init Inputs
        if mode == "INIT":
            # Browse
            dlg = ui.createFolderDialog()
            dlg.title = "Select ZenExport Base Directory"
            if dlg.showDialog() != adsk.core.DialogResults.DialogOK: return
            base_dir = dlg.folder
            
            # Name
            res = ui.inputBox("Project Name:", "New ZenExport Project", design_name)
            if res[1]: return
            project_name = sanitize_filename(res[0])
            if not project_name: return
            
            project_folder = os.path.join(base_dir, project_name)
            if os.path.exists(project_folder):
                if ui.messageBox(f"Exists:\n{project_folder}\nOverwrite?", "Warn", 3, 2) != 2: return

        # 4. Run Export
        res = perform_sync_export(app, design, project_folder, project_name)

        # 5. Persist
        save_config(project_name, project_folder)
        
        # 6. Auto-Open Explorer
        try:
            os.startfile(project_folder)
        except Exception as e:
            log_to_console(app, f"Failed to open explorer: {e}")

        # 7. Notify
        msg = (f"ZenExport Complete ({res['version']})!\n"
               f"Folder: {project_folder}\n"
               f"Preview saved.\n"
               f"STL: {res['stl_ok']} exported.")
        
        if mode == "INIT":
            ui.messageBox(msg, "Success")
        else:
            log_to_console(app, f"Update Success: {res['version']} + {res['stl_ok']} STLs")

    except:
        if ui:
            ui.messageBox(f"Failed:\n{traceback.format_exc()}")
            log_to_console(app, traceback.format_exc())
