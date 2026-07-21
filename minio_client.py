from urllib.parse import urlparse

from minio import Minio

import logger_conf as logger

log = logger.log

def _norm_endpoint(endpoint):
    if "://" in endpoint:
        return urlparse(endpoint).netloc
    return endpoint

def list_directory(endpoint, access_key, secret_key, bucket, secure, directory):
    """按目录前缀列举 MinIO 直接文件，返回相对文件名列表。"""
    log.info("遍历 MinIO 目录 endpoint=%s bucket=%s secure=%s directory=%s",
             _norm_endpoint(endpoint), bucket, secure, directory)
    client = Minio(
        _norm_endpoint(endpoint),
        access_key=access_key,
        secret_key=secret_key,
        secure=bool(secure),
    )
    prefix = directory.strip("/") + "/"
    names = []
    try:
        for obj in client.list_objects(bucket, prefix=prefix, recursive=False):
            name = obj.object_name
            if not name or name.endswith("/"):
                continue
            if name.startswith(prefix):
                rel = name[len(prefix):]
                if rel:
                    names.append(rel)
    except Exception as e:
        log.error("MinIO 遍历失败: %s", e)
        raise
    log.info("MinIO 目录 %s 共列出 %d 个文件", directory, len(names))
    return names
