"""Private object storage adapters. Credentials are read only from server env."""

import os
from pathlib import Path
from typing import BinaryIO, Protocol

import oss2


class ObjectStore(Protocol):
    def put_file(self, key: str, path: Path, content_type: str) -> None: ...

    def get_object(self, key: str) -> BinaryIO: ...

    def delete_object(self, key: str) -> None: ...


class UnconfiguredObjectStore:
    def put_file(self, key: str, path: Path, content_type: str) -> None:
        raise RuntimeError("OSS is not configured")

    def get_object(self, key: str) -> BinaryIO:
        raise RuntimeError("OSS is not configured")

    def delete_object(self, key: str) -> None:
        raise RuntimeError("OSS is not configured")


class AliyunObjectStore:
    def __init__(self, endpoint: str, bucket_name: str, region: str, access_key_id: str, access_key_secret: str):
        self.bucket = oss2.Bucket(
            oss2.AuthV4(access_key_id, access_key_secret),
            endpoint,
            bucket_name,
            region=region,
        )

    def put_file(self, key: str, path: Path, content_type: str) -> None:
        self.bucket.put_object_from_file(key, str(path), headers={"Content-Type": content_type})

    def get_object(self, key: str) -> BinaryIO:
        return self.bucket.get_object(key)

    def delete_object(self, key: str) -> None:
        self.bucket.delete_object(key)


def configured_object_store() -> ObjectStore:
    access_key_id = os.getenv("OSS_ACCESS_KEY_ID")
    access_key_secret = os.getenv("OSS_ACCESS_KEY_SECRET")
    bucket_name = os.getenv("OSS_BUCKET")
    if not all((access_key_id, access_key_secret, bucket_name)):
        return UnconfiguredObjectStore()

    region = os.getenv("OSS_REGION", "cn-shanghai")
    endpoint = os.getenv("OSS_ENDPOINT", f"https://oss-{region}.aliyuncs.com")
    return AliyunObjectStore(endpoint, bucket_name, region, access_key_id, access_key_secret)
