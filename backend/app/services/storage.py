import os
import uuid
from pathlib import Path
from fastapi import UploadFile
from ..config import settings


def save_upload(file: UploadFile) -> str:
    """Save uploaded file to local upload directory and return filesystem path.

    This is production-ready local storage. Replace with S3 adapter if desired
    but keep the same function signature.
    """
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    suffix = Path(file.filename).suffix
    filename = f"upload_{uuid.uuid4().hex}{suffix}"
    save_path = Path(settings.UPLOAD_DIR) / filename

    with save_path.open("wb") as f:
        content = file.file.read()
        f.write(content)

    return str(save_path)


__all__ = ["save_upload"]
