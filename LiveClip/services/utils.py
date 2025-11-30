import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def env(name: str, default: str = None) -> str:
    val = os.getenv(name, default)
    if val is None:
        raise RuntimeError(f"Missing env var: {name}")
    return val

def timestamp_slug() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")

def vertical_filter(width=1080, height=1920):
    # 9:16 vertical; auto scale then center crop
    return f"scale={width}:-2, pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black, crop={width}:{height}"