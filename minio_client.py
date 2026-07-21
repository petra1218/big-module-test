from urllib.parse import urlparse

from minio import Minio

def _norm_endpoint(endpoint):
    if "://" in endpoint:
        return urlparse(endpoint).netloc
    return endpoint

def list_directory(endpoint, access_key, secret_key, bucket, secure, directory):
    """按目录前缀列举 MinIO 直接文件，返回相对文件名列表。"""
    client = Minio(
        _norm_endpoint(endpoint),
        access_key=access_key,
        secret_key=secret_key,
        secure=bool(secure),
    )
    prefix = directory.strip("/") + "/"
    names = []
    for obj in client.list_objects(bucket, prefix=prefix, recursive=False):
        name = obj.object_name
        if not name or name.endswith("/"):
            continue
        if name.startswith(prefix):
            rel = name[len(prefix):]
            if rel:
                names.append(rel)
    return names
