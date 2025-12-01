# app/edge_ai/core/profile_store.py
from pathlib import Path
import json
from time import time
from app.edge_ai.schemas.profile import DeviceProfile

PROFILE_DIR = Path("data/edge_profiles")
PROFILE_DIR.mkdir(parents=True, exist_ok=True)

def load_profile(device_id: str) -> DeviceProfile:
    path = PROFILE_DIR / f"{device_id}.json"
    if not path.exists():
        return DeviceProfile(device_id=device_id)
    data = json.loads(path.read_text(encoding="utf-8"))
    return DeviceProfile(**data)

def save_profile(profile: DeviceProfile) -> None:
    profile.last_updated_ts = time()
    path = PROFILE_DIR / f"{profile.device_id}.json"
    path.write_text(profile.model_dump_json(indent=2, ensure_ascii=False),
                    encoding="utf-8")
