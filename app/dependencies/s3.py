from typing import cast

from fastapi import Request

from app.db.s3 import S3Client


def get_s3_client(request: Request) -> S3Client:
    return cast(S3Client, request.app.state.s3)
