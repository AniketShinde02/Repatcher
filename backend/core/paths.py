"""
Centralized Runtime Configuration & Path Resolver
Dynamically scans and matches weight directories, staging folders, and logs.
Supports relocation suitable for Tauri packaging.
"""

import os
from pathlib import Path
from torch.hub import get_dir

# 1. Resolve Project Root
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()

# 2. Resolve Temp & Staging Directories
TEMP_DIR = PROJECT_ROOT / "backend" / "temp"
STAGE_INPUT = TEMP_DIR / "stage_input"
STAGE_OUTPUT = TEMP_DIR / "stage_output"
STAGE_MASK = TEMP_DIR / "stage_mask"

def init_staging_dirs():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    STAGE_INPUT.mkdir(exist_ok=True)
    STAGE_OUTPUT.mkdir(exist_ok=True)
    STAGE_MASK.mkdir(exist_ok=True)

# 3. Dynamic Model Weights Discovery
def get_model_search_paths() -> list[Path]:
    """Returns a list of directories where model weights might be stored."""
    paths = []
    
    # Check environment variable MODEL_DIR first
    env_model_dir = os.getenv("MODEL_DIR")
    if env_model_dir:
        paths.append(Path(env_model_dir))
        
    # Check active torch hub directory
    try:
        torch_hub = Path(get_dir()) / "checkpoints"
        paths.append(torch_hub)
    except Exception:
        pass
        
    # Check standard Windows user profile caches
    home = Path.home()
    paths.append(home / ".cache" / "torch" / "hub" / "checkpoints")
    
    # Check local fallback inside workspace
    paths.append(PROJECT_ROOT / "backend" / "models")
    
    # Flatten and deduplicate paths
    deduped = []
    for p in paths:
        try:
            resolved = p.resolve()
            if resolved not in deduped:
                deduped.append(resolved)
        except Exception:
            pass
    return deduped

def discover_model_file(filename: str) -> Path | None:
    """Scans all search paths to locate a specific model weight file."""
    search_dirs = get_model_search_paths()
    for directory in search_dirs:
        candidate = directory / filename
        if candidate.exists() and candidate.is_file():
            # If found, configure TORCH_HOME dynamically so iopaint finds it
            try:
                # iopaint/torch hub resolves to TORCH_HOME/hub/checkpoints
                # so we point TORCH_HOME to the grandparent of the checkpoint file
                grandparent = directory.parent.parent
                os.environ["TORCH_HOME"] = str(grandparent)
            except Exception:
                pass
            return candidate
    return None

def get_checkpoints_dir() -> Path:
    """Returns the primary directory where new downloads should be placed."""
    env_model_dir = os.getenv("MODEL_DIR")
    if env_model_dir:
        p = Path(env_model_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p
    
    # Fallback to default torch hub checkpoints dir
    try:
        p = Path(get_dir()) / "checkpoints"
        p.mkdir(parents=True, exist_ok=True)
        return p
    except Exception:
        p = PROJECT_ROOT / "backend" / "models"
        p.mkdir(parents=True, exist_ok=True)
        return p
