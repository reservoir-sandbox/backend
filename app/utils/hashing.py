from hashlib import sha256
from typing import BinaryIO


def calculate_sha256(file_stream: BinaryIO) -> str:
    hasher = sha256()
    file_stream.seek(0)
    for chunk in iter(lambda: file_stream.read(65536), b""):
        hasher.update(chunk)
    file_stream.seek(0)
    return hasher.hexdigest()
