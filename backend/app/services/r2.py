import boto3
from botocore.client import Config
from fastapi import HTTPException, status

from app.config import settings


def _get_r2_client():
    endpoint = settings.r2_endpoint or (f"https://{settings.r2_account_id}.r2.cloudflarestorage.com" if settings.r2_account_id else None)

    if not all([settings.r2_access_key_id, settings.r2_secret_access_key, settings.r2_bucket, endpoint]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='R2 is not configured')

    return boto3.client(
        's3',
        endpoint_url=endpoint,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        config=Config(signature_version='s3v4'),
        region_name='auto',
    )


def generate_signed_upload_url(object_key: str, mime: str) -> str:
    client = _get_r2_client()
    return client.generate_presigned_url(
        ClientMethod='put_object',
        Params={
            'Bucket': settings.r2_bucket,
            'Key': object_key,
            'ContentType': mime,
        },
        ExpiresIn=900,
    )


def generate_signed_download_url(object_key: str) -> str:
    client = _get_r2_client()
    return client.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': settings.r2_bucket,
            'Key': object_key,
        },
        ExpiresIn=900,
    )
