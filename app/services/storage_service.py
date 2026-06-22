from typing import BinaryIO

from botocore.exceptions import BotoCoreError, ClientError

from app.db import S3Client


class StorageService:
    def __init__(self, s3_client: S3Client):
        self.s3_client = s3_client

    async def upload_file(self, body: BinaryIO, object_name: str) -> None:
        try:
            async with self.s3_client.get_client() as client:
                response = await client.put_object(
                    Bucket=self.s3_client.bucket_name,
                    Key=object_name,
                    Body=body,
                    ContentType="application/octet-stream",
                )  # pyright: ignore[reportGeneralTypeIssues]

                status_code = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
                if status_code != 200:
                    raise RuntimeError(
                        f"Failed to upload file to S3. Status code: {status_code}"
                    )
        except (BotoCoreError, ClientError) as e:
            raise RuntimeError(f"Failed to upload file to S3: {e}") from e
