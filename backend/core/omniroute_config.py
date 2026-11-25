import os
import json
from pathlib import Path
from cryptography.fernet import Fernet
import base64

# Config file locations
CONFIG_DIR = Path("./.config")
CONFIG_FILE = CONFIG_DIR / "omniroute_settings.json"
KEY_FILE = CONFIG_DIR / ".secret_key"

def _get_or_create_key() -> bytes:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not KEY_FILE.exists():
        key = Fernet.generate_key()
        KEY_FILE.write_bytes(key)
    else:
        key = KEY_FILE.read_bytes()
    return key

def _get_fernet() -> Fernet:
    return Fernet(_get_or_create_key())

def load_settings() -> dict:
    defaults = {
        "OMNIROUTE_ENABLED": False,
        "OMNIROUTE_BASE_URL": "http://localhost:20128/v1",
        "OMNIROUTE_API_KEY": "",
        "OMNIROUTE_VISION_MODEL": "auto/vision:free",
        "OMNIROUTE_TIMEOUT_MS": 30000,
        "OMNIROUTE_MAX_RETRIES": 2
    }
    
    if not CONFIG_FILE.exists():
        return defaults
        
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            
        # Decrypt API key
        if data.get("OMNIROUTE_API_KEY"):
            try:
                f_obj = _get_fernet()
                decrypted = f_obj.decrypt(data["OMNIROUTE_API_KEY"].encode()).decode()
                data["OMNIROUTE_API_KEY"] = decrypted
            except Exception:
                data["OMNIROUTE_API_KEY"] = "" # Corrupted or wrong key
                
        # Merge with defaults
        for k, v in defaults.items():
            if k not in data:
                data[k] = v
                
        return data
    except Exception:
        return defaults

def save_settings(settings: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    current = load_settings()
    current.update(settings)
    
    data_to_save = current.copy()
    
    # Encrypt API key
    if data_to_save.get("OMNIROUTE_API_KEY"):
        f_obj = _get_fernet()
        encrypted = f_obj.encrypt(data_to_save["OMNIROUTE_API_KEY"].encode()).decode()
        data_to_save["OMNIROUTE_API_KEY"] = encrypted
        
    with open(CONFIG_FILE, "w") as f:
        json.dump(data_to_save, f, indent=2)

def get_masked_settings() -> dict:
    """Returns settings suitable for returning to the frontend (masks API key)."""
    settings = load_settings()
    api_key = settings.get("OMNIROUTE_API_KEY", "")
    if api_key:
        masked_len = max(0, len(api_key) - 4)
        settings["OMNIROUTE_API_KEY"] = ("*" * masked_len) + api_key[-4:]
    return settings
