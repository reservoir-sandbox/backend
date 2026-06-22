from contextlib import asynccontextmanager

from aiobotocore.session import get_session

from app.core.config import get_settings


class S3Client:
    def __init__(
        self,
        access_key: str,
        secret_key: str,
        endpoint_url: str,
        bucket_name: str,
    ):
        self.config = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "endpoint_url": endpoint_url,
        }
        self.bucket_name = bucket_name
        self.session = get_session()

    @asynccontextmanager
    async def get_client(self):
        async with self.session.create_client("s3", **self.config) as client:
            yield client

    # async def upload_file(
    #         self,
    #         file_path: str,
    #         ) -> None:
    #     object_name = file_path.split("/")[-1]
    #     async with self.get_client() as client:
    #         with open(file_path, "rb") as file:
    #             await client.put_object(
    #                 Bucket=self.bucket_name,
    #                 Key=object_name,
    #                 Body=file,
    #             ) # pyright: ignore[reportGeneralTypeIssues]


settings = get_settings()
s3_client = S3Client(
    access_key=settings.s3_access_key,
    secret_key=settings.s3_secret_key,
    endpoint_url=settings.s3_endpoint_url,
    bucket_name=settings.s3_bucket_name,
)


def get_s3_client() -> S3Client:
    return s3_client
