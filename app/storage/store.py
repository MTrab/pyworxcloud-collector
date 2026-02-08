
from pathlib import Path
import zipfile

def export_zip(session_dir: Path, out_path: Path):
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in session_dir.iterdir():
            z.write(f, f.name)
